/**
 * Tarihi Yarımada CBS - İç Mekan Navigasyon Modülü
 * Cesium tabanlı iç mekan gezinti sistemi
 * 
 * Özellikler:
 * - İç mekan bölgeleri arası geçiş
 * - Otomatik tur modu
 * - Giriş kapısından başlayan navigasyon
 * - Serbest gezinti modu
 */

const InteriorNavigation = (function() {
    // State
    let viewer = null;
    let currentBuilding = null;
    let currentZone = null;
    let zones = [];
    let tourMode = false;
    let tourInterval = null;
    let tourIndex = 0;
    let interiorTileset = null;
    let isInsideMode = false;

    // Molla Hüsrev Camii varsayılan iç mekan bölgeleri
    // (Gerçek veriler API'den yüklenecek)
    const DEFAULT_ZONES = [
        {
            id: 1,
            name: 'Ana Giriş Kapısı',
            nameEn: 'Main Entrance',
            type: 'giris',
            description: 'Caminin ana giriş kapısı - İç mekan turunun başlangıç noktası',
            isEntrance: true,
            order: 1,
            duration: 5,
            camera: {
                longitude: 28.95925,
                latitude: 41.01345,
                height: 53,
                heading: 0,
                pitch: -15,
                roll: 0
            },
            target: {
                longitude: 28.95930,
                latitude: 41.01350,
                height: 51
            }
        },
        {
            id: 2,
            name: 'Son Cemaat Yeri',
            nameEn: 'Last Congregation Area',
            type: 'galeri',
            description: 'Giriş sonrası son cemaat mahalli',
            isEntrance: false,
            order: 2,
            duration: 8,
            camera: {
                longitude: 28.95928,
                latitude: 41.01348,
                height: 54,
                heading: 45,
                pitch: -20,
                roll: 0
            },
            target: {
                longitude: 28.95933,
                latitude: 41.01353,
                height: 52
            }
        },
        {
            id: 3,
            name: 'İbadet Alanı',
            nameEn: 'Main Prayer Hall',
            type: 'ana_mekan',
            description: 'Caminin ana ibadet alanı - Kubbe ve mihrap görünümü',
            isEntrance: false,
            order: 3,
            duration: 15,
            camera: {
                longitude: 28.95935,
                latitude: 41.01355,
                height: 55,
                heading: 90,
                pitch: -30,
                roll: 0
            },
            target: {
                longitude: 28.95940,
                latitude: 41.01360,
                height: 60
            }
        },
        {
            id: 4,
            name: 'Mihrap',
            nameEn: 'Mihrab',
            type: 'ana_mekan',
            description: 'Kıble yönünü gösteren mihrap nişi',
            isEntrance: false,
            order: 4,
            duration: 10,
            camera: {
                longitude: 28.95942,
                latitude: 41.01362,
                height: 53,
                heading: 135,
                pitch: -10,
                roll: 0
            },
            target: {
                longitude: 28.95945,
                latitude: 41.01365,
                height: 52
            }
        },
        {
            id: 5,
            name: 'Minber',
            nameEn: 'Minbar',
            type: 'ana_mekan',
            description: 'Hutbe okunan minber',
            isEntrance: false,
            order: 5,
            duration: 8,
            camera: {
                longitude: 28.95940,
                latitude: 41.01358,
                height: 54,
                heading: 180,
                pitch: -25,
                roll: 0
            },
            target: {
                longitude: 28.95945,
                latitude: 41.01363,
                height: 55
            }
        }
    ];

    // UI Elements referansları
    const UI = {
        container: null,
        zonePanel: null,
        zoneList: null,
        tourButton: null,
        exitButton: null,
        infoOverlay: null,
        progressBar: null
    };

    /**
     * Modülü başlat
     * @param {Cesium.Viewer} cesiumViewer - Cesium Viewer instance
     */
    function initialize(cesiumViewer) {
        if (!cesiumViewer) {
            console.error('InteriorNavigation: Cesium Viewer gerekli');
            return false;
        }

        viewer = cesiumViewer;
        zones = [...DEFAULT_ZONES];
        
        // UI oluştur
        createUI();
        
        // Event listener'ları kur
        setupEventListeners();

        console.log('İç Mekan Navigasyon modülü başlatıldı');
        return true;
    }

    /**
     * UI bileşenlerini oluştur
     */
    function createUI() {
        // Ana container
        UI.container = document.createElement('div');
        UI.container.id = 'interior-nav-container';
        UI.container.className = 'interior-nav-container hidden';
        UI.container.innerHTML = `
            <div class="interior-nav-panel">
                <div class="interior-nav-header">
                    <div class="interior-nav-title">
                        <span class="interior-icon">🏛️</span>
                        <h3>İç Mekan Gezinti</h3>
                    </div>
                    <button class="interior-nav-close" id="interior-nav-close" title="Dış Mekana Dön">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>
                
                <div class="interior-nav-info">
                    <p id="interior-building-name">Molla Hüsrev Camii</p>
                    <span class="interior-badge">İç Mekan Modu</span>
                </div>
                
                <div class="interior-nav-actions">
                    <button class="interior-action-btn primary" id="btn-start-tour">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                            <polygon points="5 3 19 12 5 21 5 3"></polygon>
                        </svg>
                        Otomatik Tur Başlat
                    </button>
                    <button class="interior-action-btn" id="btn-go-entrance">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                            <polyline points="9 22 9 12 15 12 15 22"></polyline>
                        </svg>
                        Giriş Kapısına Git
                    </button>
                </div>
                
                <div class="interior-nav-zones">
                    <h4>📍 Bölgeler</h4>
                    <div class="zone-list" id="zone-list">
                        <!-- Bölgeler JavaScript ile doldurulacak -->
                    </div>
                </div>
                
                <div class="interior-nav-progress hidden" id="tour-progress">
                    <div class="progress-info">
                        <span id="tour-current-zone">-</span>
                        <span id="tour-counter">0 / 0</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="tour-progress-fill"></div>
                    </div>
                    <div class="progress-actions">
                        <button class="progress-btn" id="btn-tour-prev" title="Önceki">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                                <polyline points="15 18 9 12 15 6"></polyline>
                            </svg>
                        </button>
                        <button class="progress-btn" id="btn-tour-pause" title="Duraklat/Devam">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                                <rect x="6" y="4" width="4" height="16"></rect>
                                <rect x="14" y="4" width="4" height="16"></rect>
                            </svg>
                        </button>
                        <button class="progress-btn" id="btn-tour-next" title="Sonraki">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                                <polyline points="9 18 15 12 9 6"></polyline>
                            </svg>
                        </button>
                        <button class="progress-btn danger" id="btn-tour-stop" title="Turu Bitir">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="interior-zone-info hidden" id="zone-info-overlay">
                <div class="zone-info-content">
                    <h4 id="zone-info-name">-</h4>
                    <p id="zone-info-desc">-</p>
                    <span class="zone-info-type" id="zone-info-type">-</span>
                </div>
            </div>
        `;

        document.body.appendChild(UI.container);

        // Referansları kaydet
        UI.zoneList = document.getElementById('zone-list');
        UI.tourButton = document.getElementById('btn-start-tour');
        UI.exitButton = document.getElementById('interior-nav-close');
        UI.infoOverlay = document.getElementById('zone-info-overlay');
        UI.progressBar = document.getElementById('tour-progress');
    }

    /**
     * Event listener'ları kur
     */
    function setupEventListeners() {
        // Çıkış butonu
        document.getElementById('interior-nav-close')?.addEventListener('click', exitInterior);
        
        // Tur başlat
        document.getElementById('btn-start-tour')?.addEventListener('click', startTour);
        
        // Giriş kapısına git
        document.getElementById('btn-go-entrance')?.addEventListener('click', goToEntrance);
        
        // Tur kontrolleri
        document.getElementById('btn-tour-prev')?.addEventListener('click', previousZone);
        document.getElementById('btn-tour-next')?.addEventListener('click', nextZone);
        document.getElementById('btn-tour-pause')?.addEventListener('click', toggleTourPause);
        document.getElementById('btn-tour-stop')?.addEventListener('click', stopTour);
    }

    /**
     * Bölge listesini oluştur
     */
    function renderZoneList() {
        if (!UI.zoneList) return;

        const sortedZones = [...zones].sort((a, b) => a.order - b.order);
        
        UI.zoneList.innerHTML = sortedZones.map(zone => `
            <div class="zone-item ${zone.isEntrance ? 'entrance' : ''} ${currentZone?.id === zone.id ? 'active' : ''}" 
                 data-zone-id="${zone.id}">
                <div class="zone-item-icon">
                    ${getZoneIcon(zone.type)}
                </div>
                <div class="zone-item-info">
                    <span class="zone-item-name">${zone.name}</span>
                    <span class="zone-item-type">${getZoneTypeName(zone.type)}</span>
                </div>
                <div class="zone-item-arrow">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                        <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                </div>
            </div>
        `).join('');

        // Bölge tıklama olayları
        UI.zoneList.querySelectorAll('.zone-item').forEach(item => {
            item.addEventListener('click', () => {
                const zoneId = parseInt(item.dataset.zoneId);
                navigateToZone(zoneId);
            });
        });
    }

    /**
     * Bölge tipi için ikon döndür
     */
    function getZoneIcon(type) {
        const icons = {
            'giris': '🚪',
            'ana_mekan': '🕌',
            'galeri': '🏛️',
            'koridor': '🚶',
            'merdiven': '🪜',
            'kubbe': '⭕'
        };
        return icons[type] || '📍';
    }

    /**
     * Bölge tipi için Türkçe isim döndür
     */
    function getZoneTypeName(type) {
        const names = {
            'giris': 'Giriş',
            'ana_mekan': 'Ana Mekân',
            'galeri': 'Galeri',
            'koridor': 'Koridor',
            'merdiven': 'Merdiven',
            'kubbe': 'Kubbe Altı'
        };
        return names[type] || 'Bölge';
    }

    /**
     * İç mekan moduna gir
     * @param {number} buildingId - Yapı ID
     * @param {number} ionAssetId - Cesium Ion Asset ID (opsiyonel)
     */
    async function enterInterior(buildingId, ionAssetId = null) {
        if (!viewer) {
            console.error('Viewer başlatılmamış');
            return false;
        }

        currentBuilding = buildingId;
        isInsideMode = true;

        // Bölgeleri API'den yükle (varsa)
        await loadZonesFromAPI(buildingId);

        // İç mekan 3D Tiles yükle (varsa)
        if (ionAssetId) {
            await loadInteriorTileset(ionAssetId);
        }

        // UI'ı göster
        UI.container?.classList.remove('hidden');
        
        // Bölge listesini render et
        renderZoneList();

        // Giriş noktasına uç
        goToEntrance();

        // Header'da iç mekan modunu göster
        document.querySelector('.nav-btn[data-view="potree"]')?.classList.add('active');
        document.querySelector('.viewer-overlay .location-text')?.textContent && 
            (document.querySelector('.viewer-overlay .location-text').textContent = 'Molla Hüsrev Camii - İç Mekan');

        console.log('İç mekan moduna girildi, Yapı ID:', buildingId);
        return true;
    }

    /**
     * API'den bölgeleri yükle
     */
    async function loadZonesFromAPI(buildingId) {
        try {
            const response = await fetch(`/api/v1/yapilar/${buildingId}/ic-mekan-bolgeler`);
            if (response.ok) {
                const data = await response.json();
                if (data && data.length > 0) {
                    zones = data.map(z => ({
                        id: z.id,
                        name: z.bolge_adi,
                        nameEn: z.bolge_adi_en,
                        type: z.bolge_turu,
                        description: z.aciklama,
                        isEntrance: z.giris_noktasi,
                        order: z.siralama,
                        duration: z.gezinti_suresi,
                        camera: {
                            longitude: z.kamera_lon,
                            latitude: z.kamera_lat,
                            height: z.kamera_height,
                            heading: z.kamera_heading,
                            pitch: z.kamera_pitch,
                            roll: z.kamera_roll || 0
                        },
                        target: {
                            longitude: z.hedef_lon,
                            latitude: z.hedef_lat,
                            height: z.hedef_height
                        }
                    }));
                    console.log('Bölgeler API\'den yüklendi:', zones.length);
                }
            }
        } catch (error) {
            console.warn('API\'den bölgeler yüklenemedi, varsayılan bölgeler kullanılıyor:', error);
        }
    }

    /**
     * İç mekan 3D Tiles yükle
     */
    async function loadInteriorTileset(ionAssetId) {
        try {
            interiorTileset = await Cesium.Cesium3DTileset.fromIonAssetId(ionAssetId, {
                maximumScreenSpaceError: 4,
                maximumMemoryUsage: 512
            });
            viewer.scene.primitives.add(interiorTileset);
            console.log('İç mekan tileset yüklendi, Asset ID:', ionAssetId);
        } catch (error) {
            console.warn('İç mekan tileset yüklenemedi:', error);
        }
    }

    /**
     * İç mekandan çık
     */
    function exitInterior() {
        isInsideMode = false;
        currentBuilding = null;
        currentZone = null;

        // Turu durdur
        stopTour();

        // UI'ı gizle
        UI.container?.classList.add('hidden');
        UI.infoOverlay?.classList.add('hidden');

        // Dış mekana dön
        if (typeof CesiumViewer !== 'undefined') {
            CesiumViewer.flyToHome();
        }

        // Header'ı güncelle
        document.querySelector('.nav-btn[data-view="cesium"]')?.classList.add('active');
        document.querySelector('.nav-btn[data-view="potree"]')?.classList.remove('active');

        console.log('İç mekan modundan çıkıldı');
    }

    /**
     * Giriş kapısına git
     */
    function goToEntrance() {
        const entranceZone = zones.find(z => z.isEntrance);
        if (entranceZone) {
            navigateToZone(entranceZone.id);
        } else if (zones.length > 0) {
            navigateToZone(zones[0].id);
        }
    }

    /**
     * Belirli bir bölgeye git
     * @param {number} zoneId - Bölge ID
     * @param {number} duration - Uçuş süresi (saniye)
     */
    function navigateToZone(zoneId, duration = 2.0) {
        const zone = zones.find(z => z.id === zoneId);
        if (!zone || !viewer) return;

        currentZone = zone;

        // Kamera pozisyonunu ayarla
        const { camera, target } = zone;
        
        viewer.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(
                camera.longitude,
                camera.latitude,
                camera.height
            ),
            orientation: {
                heading: Cesium.Math.toRadians(camera.heading),
                pitch: Cesium.Math.toRadians(camera.pitch),
                roll: Cesium.Math.toRadians(camera.roll || 0)
            },
            duration: duration,
            complete: () => {
                showZoneInfo(zone);
            }
        });

        // Aktif bölgeyi güncelle
        updateActiveZone(zoneId);
        
        console.log('Bölgeye gidiliyor:', zone.name);
    }

    /**
     * Aktif bölgeyi UI'da güncelle
     */
    function updateActiveZone(zoneId) {
        UI.zoneList?.querySelectorAll('.zone-item').forEach(item => {
            item.classList.toggle('active', parseInt(item.dataset.zoneId) === zoneId);
        });
    }

    /**
     * Bölge bilgisini göster
     */
    function showZoneInfo(zone) {
        if (!UI.infoOverlay) return;

        document.getElementById('zone-info-name').textContent = zone.name;
        document.getElementById('zone-info-desc').textContent = zone.description;
        document.getElementById('zone-info-type').textContent = getZoneTypeName(zone.type);

        UI.infoOverlay.classList.remove('hidden');

        // 5 saniye sonra gizle (tur modunda değilse)
        if (!tourMode) {
            setTimeout(() => {
                UI.infoOverlay?.classList.add('hidden');
            }, 5000);
        }
    }

    /**
     * Otomatik turu başlat
     */
    function startTour() {
        if (zones.length === 0) {
            console.warn('Tur için bölge bulunamadı');
            return;
        }

        tourMode = true;
        tourIndex = 0;

        // UI'ı güncelle
        UI.progressBar?.classList.remove('hidden');
        UI.tourButton?.classList.add('hidden');

        // İlk bölgeye git
        runTourStep();

        console.log('Otomatik tur başladı');
    }

    /**
     * Tur adımını çalıştır
     */
    function runTourStep() {
        if (!tourMode || tourIndex >= zones.length) {
            stopTour();
            return;
        }

        const sortedZones = [...zones].sort((a, b) => a.order - b.order);
        const zone = sortedZones[tourIndex];

        // Progress güncelle
        updateTourProgress(zone, tourIndex + 1, sortedZones.length);

        // Bölgeye git
        navigateToZone(zone.id, 2.0);

        // Sonraki bölgeye geç
        tourInterval = setTimeout(() => {
            tourIndex++;
            runTourStep();
        }, (zone.duration + 2) * 1000); // Bekleme + uçuş süresi
    }

    /**
     * Tur progress'ini güncelle
     */
    function updateTourProgress(zone, current, total) {
        document.getElementById('tour-current-zone').textContent = zone.name;
        document.getElementById('tour-counter').textContent = `${current} / ${total}`;
        
        const progress = (current / total) * 100;
        const progressFill = document.getElementById('tour-progress-fill');
        if (progressFill) {
            progressFill.style.width = `${progress}%`;
        }
    }

    /**
     * Turu durdur
     */
    function stopTour() {
        tourMode = false;
        
        if (tourInterval) {
            clearTimeout(tourInterval);
            tourInterval = null;
        }

        // UI'ı güncelle
        UI.progressBar?.classList.add('hidden');
        UI.tourButton?.classList.remove('hidden');
        UI.infoOverlay?.classList.add('hidden');

        console.log('Tur durduruldu');
    }

    /**
     * Turu duraklat/devam et
     */
    function toggleTourPause() {
        if (!tourMode) return;

        if (tourInterval) {
            clearTimeout(tourInterval);
            tourInterval = null;
            document.getElementById('btn-tour-pause').innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                </svg>
            `;
        } else {
            const sortedZones = [...zones].sort((a, b) => a.order - b.order);
            const zone = sortedZones[tourIndex];
            tourInterval = setTimeout(() => {
                tourIndex++;
                runTourStep();
            }, (zone.duration + 2) * 1000);
            document.getElementById('btn-tour-pause').innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                    <rect x="6" y="4" width="4" height="16"></rect>
                    <rect x="14" y="4" width="4" height="16"></rect>
                </svg>
            `;
        }
    }

    /**
     * Önceki bölge
     */
    function previousZone() {
        if (!tourMode) return;

        const sortedZones = [...zones].sort((a, b) => a.order - b.order);
        tourIndex = Math.max(0, tourIndex - 1);
        
        if (tourInterval) {
            clearTimeout(tourInterval);
        }
        
        runTourStep();
    }

    /**
     * Sonraki bölge
     */
    function nextZone() {
        if (!tourMode) return;

        const sortedZones = [...zones].sort((a, b) => a.order - b.order);
        tourIndex = Math.min(sortedZones.length - 1, tourIndex + 1);
        
        if (tourInterval) {
            clearTimeout(tourInterval);
        }
        
        runTourStep();
    }

    /**
     * Serbest gezinti modunu aktifleştir
     */
    function enableFreeRoam() {
        stopTour();
        
        // Kamera kontrollerini serbest bırak
        const controller = viewer.scene.screenSpaceCameraController;
        controller.enableRotate = true;
        controller.enableTilt = true;
        controller.enableZoom = true;
        controller.enableLook = true;
        
        // Sınırları daralt (iç mekanda kalması için)
        controller.minimumZoomDistance = 1;
        controller.maximumZoomDistance = 50;

        console.log('Serbest gezinti modu aktif');
    }

    /**
     * Bölge ekle (dinamik)
     */
    function addZone(zoneData) {
        zones.push(zoneData);
        renderZoneList();
    }

    /**
     * Temizle
     */
    function destroy() {
        stopTour();
        
        if (interiorTileset && viewer) {
            viewer.scene.primitives.remove(interiorTileset);
            interiorTileset = null;
        }
        
        UI.container?.remove();
        
        viewer = null;
        currentBuilding = null;
        currentZone = null;
        zones = [];
    }

    // Public API
    return {
        initialize,
        enterInterior,
        exitInterior,
        goToEntrance,
        navigateToZone,
        startTour,
        stopTour,
        enableFreeRoam,
        addZone,
        destroy,
        
        // Getters
        isInsideMode: () => isInsideMode,
        getCurrentZone: () => currentZone,
        getZones: () => [...zones],
        isTourActive: () => tourMode
    };
})();

// Global erişim
window.InteriorNavigation = InteriorNavigation;


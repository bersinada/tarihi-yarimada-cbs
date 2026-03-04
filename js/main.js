/**
 * Tarihi Yarımada CBS - Main Application
 * Yeniden Tasarlanmış Ana Uygulama Kontrolcüsü
 */

const App = (function() {
    // Uygulama durumu
    const state = {
        currentAssetId: null, // Seçili eser
        isAssetPanelOpen: false,
        isAboutPanelOpen: false,
        isBasemapPanelOpen: false,
        currentBasemap: 'satellite',
        isLoading: true,
        cesiumReady: false,
        orbitLocked: false,
        notes: [],
        interiorMode: false,
        loadedTilesets: {}, // { ionAssetId: tileset }
        renderQuality: 'low'
    };

    // DOM elementleri
    const elements = {};

    /**
     * Uygulamayı başlat
     */
    async function initialize() {
        console.log('Tarihi Yarımada CBS başlatılıyor...');
        
        cacheElements();
        setupEventListeners();
        checkAPIConnection();
        await initializeViewers();
        hideLoadingScreen();
        
        console.log('Uygulama başarıyla başlatıldı');
    }

    /**
     * DOM elementlerini cache'le
     */
    function cacheElements() {
        // Loading Screen
        elements.loadingScreen = document.getElementById('loading-screen');
        elements.app = document.getElementById('app');
        elements.loaderStatus = document.querySelector('.loader-status');
        
        // Main containers
        elements.cesiumContainer = document.getElementById('cesium-container');
        elements.mainContent = document.querySelector('.main-content');
        
        // Panels
        elements.assetPanel = document.getElementById('asset-panel');
        elements.assetPanelClose = document.getElementById('asset-panel-close');
        elements.aboutPanel = document.getElementById('about-panel');
        elements.aboutClose = document.getElementById('about-close');
        
        // Header buttons
        elements.btnAbout = document.getElementById('btn-about');
        elements.btnBasemap = document.getElementById('btn-basemap');
        elements.btnLayers = document.getElementById('btn-layers');
        elements.btnSettings = document.getElementById('btn-settings');
        
        // Dropdown menu
        elements.dropdownItems = document.querySelectorAll('.dropdown-item');

        // Modals
        elements.basemapModal = document.getElementById('basemap-modal');
        elements.layersModal = document.getElementById('layers-modal');
        
        // Floating controls
        elements.btnHome = document.getElementById('btn-home');
        elements.btnOrbit = document.getElementById('btn-orbit');
        elements.btnZoomIn = document.getElementById('btn-zoom-in');
        elements.btnZoomOut = document.getElementById('btn-zoom-out');
        elements.btnFullscreen = document.getElementById('btn-fullscreen');
        
        // Settings modal
        elements.settingsModal = document.getElementById('settings-modal');
        elements.renderQuality = document.getElementById('render-quality');
        elements.pointSize = document.getElementById('point-size');
        elements.showShadows = document.getElementById('show-shadows');
        elements.terrainEnabled = document.getElementById('terrain-enabled');
        
        // Asset panel elements
        elements.assetPanelTitle = document.getElementById('asset-panel-title');
        elements.assetName = document.getElementById('asset-name');
        elements.assetPeriod = document.getElementById('asset-period');
        elements.assetYear = document.getElementById('asset-year');
        elements.assetPeriodInfo = document.getElementById('asset-period-info');
        elements.assetFounder = document.getElementById('asset-founder');
        elements.assetLocation = document.getElementById('asset-location');
        elements.assetDescription = document.getElementById('asset-description');
        elements.assetLayers = document.getElementById('asset-layers');
        elements.locationText = document.getElementById('location-text');

        // Photo gallery
        elements.photoGallery = document.getElementById('photo-gallery');
        elements.galleryPlaceholder = document.getElementById('gallery-placeholder');

        // Notes
        elements.noteTitle = document.getElementById('note-title');
        elements.noteContent = document.getElementById('note-content');
        elements.noteAuthor = document.getElementById('note-author');
        elements.charCount = document.getElementById('char-count');
        elements.btnSaveNote = document.getElementById('btn-save-note');
        elements.btnRefreshNotes = document.getElementById('btn-refresh-notes');
        elements.notesCountNumber = document.getElementById('notes-count-number');
        elements.notesItems = document.getElementById('notes-items');

        // Asset View Controls - Harita üzerinde floating overlay
        elements.assetViewControls = document.getElementById('asset-view-controls');
        elements.btnAssetOrbit = document.getElementById('btn-asset-orbit');
        elements.btnAssetZoom = document.getElementById('btn-asset-zoom');
        elements.btnAssetClose = document.getElementById('btn-asset-close');
    }

    /**
     * Event listener'ları kur
     */
    function setupEventListeners() {
        // Dropdown items - Eser seçimi
        elements.dropdownItems.forEach(item => {
            item.addEventListener('click', () => {
                const assetId = item.dataset.asset;
                selectAsset(assetId);
            });
        });
        
        // About button
        if (elements.btnAbout) {
            elements.btnAbout.addEventListener('click', toggleAboutPanel);
        }
        
        // Asset panel close
        if (elements.assetPanelClose) {
            elements.assetPanelClose.addEventListener('click', closeAssetPanel);
        }
        
        // About panel close
        if (elements.aboutClose) {
            elements.aboutClose.addEventListener('click', closeAboutPanel);
        }
        
        // Basemap button
        if (elements.btnBasemap) {
            elements.btnBasemap.addEventListener('click', () => openModal('basemap-modal'));
        }

        // Layers button
        if (elements.btnLayers) {
            elements.btnLayers.addEventListener('click', () => openModal('layers-modal'));
        }

        // Settings button
        if (elements.btnSettings) {
            elements.btnSettings.addEventListener('click', () => openModal('settings-modal'));
        }

        // Basemap options
        document.querySelectorAll('.basemap-option').forEach(option => {
            option.addEventListener('click', () => {
                const basemapId = option.dataset.basemap;
                handleBasemapChange(basemapId);
            });
        });

        // Layer checkboxes in modal
        document.querySelectorAll('#layers-modal input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const layerType = e.target.dataset.layer;
                handleLayerToggle(layerType, e.target.checked);
            });
        });
        
        // Floating controls
        if (elements.btnHome) {
            elements.btnHome.addEventListener('click', handleHomeClick);
        }
        if (elements.btnOrbit) {
            elements.btnOrbit.addEventListener('click', handleOrbitToggle);
        }
        if (elements.btnZoomIn) {
            elements.btnZoomIn.addEventListener('click', handleZoomIn);
        }
        if (elements.btnZoomOut) {
            elements.btnZoomOut.addEventListener('click', handleZoomOut);
        }
        if (elements.btnFullscreen) {
            elements.btnFullscreen.addEventListener('click', handleFullscreen);
        }
        
        // Modal close buttons
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', closeAllModals);
        });
        
        // Modal backdrop click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) closeAllModals();
            });
        });
        
        // Settings controls
        if (elements.renderQuality) {
            elements.renderQuality.addEventListener('change', (e) => {
                state.renderQuality = e.target.value;
                CesiumViewer.setQuality(state.renderQuality);
            });
        }
        
        if (elements.pointSize) {
            elements.pointSize.addEventListener('input', (e) => {
                handlePointSizeChange(parseInt(e.target.value));
            });
        }
        
        if (elements.showShadows) {
            elements.showShadows.addEventListener('change', (e) => {
                CesiumViewer.setShadows(e.target.checked);
            });
        }
        
        if (elements.terrainEnabled) {
            elements.terrainEnabled.addEventListener('change', (e) => {
                CesiumViewer.setTerrain(e.target.checked);
            });
        }
        
        // Notes
        if (elements.noteContent) {
            elements.noteContent.addEventListener('input', updateCharCount);
        }
        
        if (elements.btnSaveNote) {
            elements.btnSaveNote.addEventListener('click', handleSaveNote);
        }
        
        if (elements.btnRefreshNotes) {
            elements.btnRefreshNotes.addEventListener('click', loadNotes);
        }

        // Asset View Controls - Harita üzerinde floating overlay butonları
        if (elements.btnAssetOrbit) {
            elements.btnAssetOrbit.addEventListener('click', handleAssetOrbit);
        }
        if (elements.btnAssetZoom) {
            elements.btnAssetZoom.addEventListener('click', handleAssetZoom);
        }
        if (elements.btnAssetClose) {
            elements.btnAssetClose.addEventListener('click', handleAssetClose);
        }

        // Close panel when pressing Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeAssetPanel();
                closeAboutPanel();
                closeAllModals();
            }
        });
    }

    /**
     * Viewer'ları başlat
     */
    async function initializeViewers() {
        updateLoadingStatus('Cesium Viewer hazırlanıyor...');

        try {
            // Backend'den eserleri yükle
            updateLoadingStatus('Eserler yükleniyor...');
            await AssetsData.loadAssets();

            await CesiumViewer.initialize('cesiumViewer');
            state.cesiumReady = true;
            CesiumViewer.startFPSCounter();
            CesiumViewer.setQuality(state.renderQuality);

            // Tüm eserlerin modellerini yükle (başlangıçta hepsi görünsün)
            await loadAllModels();

            // Dropdown menüsünü dinamik olarak oluştur
            populateAssetsDropdown();

            // Başlangıçta bütün yarımadayı göster ve location text'i ayarla
            if (elements.locationText) {
                elements.locationText.textContent = 'Tarihi Yarımada - İstanbul';
            }

            console.log('Harita görüntüleniyor - Tarihi Yarımada');

        } catch (error) {
            console.error('Cesium başlatılamadı:', error);
            updateLoadingStatus('Cesium yüklenirken hata oluştu');
        }
    }

    /**
     * Tüm eserlerin 3D modellerini yükle
     */
    async function loadAllModels() {
        updateLoadingStatus('3D modeller yükleniyor...');
        
        for (const asset of AssetsData.assets) {
            for (const layer of asset.ionAssetIds) {
                try {
                    const tileset = await CesiumViewer.loadFromIonAssetId(layer.id, { 
                        zoomTo: false, 
                        show: true  // Başlangıçta tüm modeller görünsün
                    });
                    state.loadedTilesets[layer.id] = tileset;
                    console.log(`Model yüklendi: ${layer.name}`);
                } catch (error) {
                    console.warn(`Model yüklenemedi: ${layer.name}`, error);
                }
            }
        }
        
        updateLoadingStatus('Tüm modeller yüklendi');
    }

    /**
     * Dropdown menüsünü backend'den yüklenen eserlerle doldur (yapı tiplerine göre grupla)
     */
    function populateAssetsDropdown() {
        const dropdownContent = document.querySelector('.dropdown-content');
        if (!dropdownContent) {
            console.warn('Dropdown content bulunamadı');
            return;
        }

        // Mevcut içeriği temizle
        dropdownContent.innerHTML = '';

        // Eserleri yapı tipine göre grupla
        const typeGroups = {};
        AssetsData.assets.forEach(asset => {
            const type = asset.buildingType || 'diger';
            if (!typeGroups[type]) {
                typeGroups[type] = [];
            }
            typeGroups[type].push(asset);
        });

        // Yapı tiplerini sıralı olarak getir
        const orderedTypes = AssetsData.getBuildingTypes();

        // Her yapı tipi için section oluştur
        orderedTypes.forEach(typeKey => {
            if (!typeGroups[typeKey] || typeGroups[typeKey].length === 0) return;

            const typeInfo = AssetsData.getBuildingTypeInfo(typeKey);
            const section = document.createElement('div');
            section.className = 'dropdown-section';

            const title = document.createElement('h4');
            title.className = 'dropdown-section-title';
            title.textContent = typeInfo.name;
            section.appendChild(title);

            // Eserleri ekle
            typeGroups[typeKey].forEach(asset => {
                const button = document.createElement('button');
                button.className = 'dropdown-item';
                button.dataset.asset = asset.id;
                button.innerHTML = `
                    <span class="asset-name">${asset.name}</span>
                    <span class="asset-period-tag">${asset.period}</span>
                `;

                // Event listener ekle
                button.addEventListener('click', () => {
                    selectAsset(asset.id);
                });

                section.appendChild(button);
            });

            dropdownContent.appendChild(section);
        });

        console.log('Dropdown menüsü yapı tiplerine göre oluşturuldu:', orderedTypes);
    }

    /**
     * Ana görünüm - tüm yarımadayı göster
     */
    function showHomeView() {
        console.log('Ana görünüme dönülüyor...');

        // Location badge'i güncelle
        if (elements.locationText) {
            elements.locationText.textContent = 'Tarihi Yarımada - İstanbul';
        }

        // Cesium viewer'a zoom at
        CesiumViewer.flyToHome();

        // Asset panel'i kapat
        closeAssetPanel();

        // Seçili asset'i temizle
        state.currentAssetId = null;
    }

    /**
     * Eseri seç
     */
    function selectAsset(assetId) {
        const asset = AssetsData.getAsset(assetId);
        if (!asset) {
            console.error('Eser bulunamadı:', assetId);
            return;
        }

        console.log('Eser seçildi:', assetId, asset);
        state.currentAssetId = assetId;

        // Location badge'i güncelle
        if (elements.locationText) {
            elements.locationText.textContent = asset.name;
        }

        // Asset panel'i aç
        openAssetPanel(asset);

        // Asset'in modelini vurgula
        highlightAssetModel(asset);

        // Kamerayı asset'e zoom at (çapraz yukarıdan)
        zoomToAsset(asset);

        // Asset view controls overlay'ini göster
        showAssetViewControls();

        // Notları yükle
        loadNotes(assetId);
    }

    /**
     * Asset panel'i aç ve bilgileri göster
     */
    function openAssetPanel(asset) {
        // Başlık ve bilgiler
        elements.assetName.textContent = asset.name;
        elements.assetPeriod.textContent = asset.period;
        // Yapım yılı - construction_period veya formatlanmış yıl
        elements.assetYear.textContent = formatYearDisplay(asset.year);
        elements.assetPeriodInfo.textContent = asset.period + ' Dönemi';
        elements.assetFounder.textContent = asset.founder;
        elements.assetLocation.textContent = asset.location;
        elements.assetDescription.textContent = asset.description;

        // 3D model katmanlarını listele
        renderAssetLayers(asset);

        // Fotoğrafları yükle
        loadAssetPhotos(asset.id);

        // Panel'i aç
        state.isAssetPanelOpen = true;
        elements.assetPanel.classList.add('open');

        updateLoadingStatus('Bilgiler yüklendi');
    }

    /**
     * Asset fotoğraflarını yükle ve göster
     */
    async function loadAssetPhotos(assetId) {
        if (!elements.photoGallery) return;

        // Placeholder'ı göster
        if (elements.galleryPlaceholder) {
            elements.galleryPlaceholder.style.display = 'flex';
            elements.galleryPlaceholder.querySelector('p').textContent = 'Fotoğraflar yükleniyor...';
        }

        // Mevcut fotoğrafları temizle (placeholder hariç)
        const existingPhotos = elements.photoGallery.querySelectorAll('.gallery-item');
        existingPhotos.forEach(item => item.remove());

        try {
            const media = await AssetsData.loadAssetMedia(assetId);
            console.log('Media loaded:', media);

            if (media && media.length > 0) {
                // Placeholder'ı gizle
                if (elements.galleryPlaceholder) {
                    elements.galleryPlaceholder.style.display = 'none';
                }

                // Fotoğrafları ekle
                const apiBaseUrl = AssetsData.getApiBaseUrl();
                console.log('API Base URL:', apiBaseUrl);
                media.forEach((item, index) => {
                    const galleryItem = document.createElement('div');
                    galleryItem.className = 'gallery-item' + (item.is_primary ? ' primary' : '');

                    const img = document.createElement('img');
                    // Relative URL'leri backend URL'si ile birleştir
                    const imgUrl = item.url.startsWith('/') ? `${apiBaseUrl}${item.url}` : item.url;
                    console.log('Image URL:', imgUrl);
                    img.src = imgUrl;
                    img.alt = item.caption || 'Fotoğraf';
                    img.loading = 'lazy';
                    img.onerror = () => {
                        galleryItem.style.display = 'none';
                    };

                    if (item.caption) {
                        const caption = document.createElement('span');
                        caption.className = 'gallery-caption';
                        caption.textContent = item.caption;
                        galleryItem.appendChild(caption);
                    }

                    galleryItem.appendChild(img);
                    elements.photoGallery.appendChild(galleryItem);
                });
            } else {
                // Fotoğraf yok
                if (elements.galleryPlaceholder) {
                    elements.galleryPlaceholder.style.display = 'flex';
                    elements.galleryPlaceholder.querySelector('p').textContent = 'Fotoğraf bulunamadı';
                }
            }
        } catch (error) {
            console.error('Fotoğraflar yüklenirken hata:', error);
            if (elements.galleryPlaceholder) {
                elements.galleryPlaceholder.style.display = 'flex';
                elements.galleryPlaceholder.querySelector('p').textContent = 'Fotoğraflar yüklenemedi';
            }
        }
    }

    /**
     * Asset panel'i kapat
     */
    function closeAssetPanel() {
        state.isAssetPanelOpen = false;
        elements.assetPanel.classList.remove('open');

        // Orbit modunu kapat
        if (state.orbitLocked) {
            state.orbitLocked = false;
            CesiumViewer.unlockOrbit();
            if (elements.btnOrbit) {
                elements.btnOrbit.classList.remove('active');
            }
            if (elements.btnAssetOrbit) {
                elements.btnAssetOrbit.classList.remove('active');
            }
        }

        // Asset view controls overlay'ini gizle
        hideAssetViewControls();

        // Seçili asset'i temizle ve home'a dön
        if (state.currentAssetId) {
            state.currentAssetId = null;
            if (elements.locationText) {
                elements.locationText.textContent = 'Tarihi Yarımada - İstanbul';
            }
            CesiumViewer.flyToHome();
        }
    }

    /**
     * Asset'in 3D model katmanlarını render et
     */
    function renderAssetLayers(asset) {
        elements.assetLayers.innerHTML = '';
        
        if (!asset.ionAssetIds || asset.ionAssetIds.length === 0) {
            elements.assetLayers.innerHTML = '<p style="color: var(--color-text-muted);">3D model yok</p>';
            return;
        }
        
        asset.ionAssetIds.forEach((layer, index) => {
            const label = document.createElement('label');
            label.className = 'layer-item';
            label.innerHTML = `
                <input type="checkbox" ${layer.visible ? 'checked' : ''} data-ion-asset-id="${layer.id}">
                <span class="layer-checkbox"></span>
                <span class="layer-name">${layer.name}</span>
                <span class="layer-type">${layer.type}</span>
            `;
            
            const input = label.querySelector('input');
            input.addEventListener('change', () => {
                toggleAssetLayer(layer.id, input.checked);
            });
            
            elements.assetLayers.appendChild(label);
        });
    }

    /**
     * Asset model katmanını aç/kapat
     */
    function toggleAssetLayer(ionAssetId, visible) {
        const tileset = state.loadedTilesets[ionAssetId];
        if (tileset) {
            tileset.show = visible;
            console.log(`Tileset ${ionAssetId} görünürlük: ${visible}`);
        }
    }

    /**
     * Asset seçildiğinde modeli vurgula (diğerlerini gizlemeden)
     */
    function highlightAssetModel(asset) {
        // Seçili asset'in modellerini göster
        for (const layer of asset.ionAssetIds) {
            const tileset = state.loadedTilesets[layer.id];
            if (tileset) {
                tileset.show = true;
            }
        }
    }

    /**
     * Yapı tipine göre kamera ayarlarını getir
     */
    function getCameraSettingsForAsset(asset) {
        // Yapı tipine göre dinamik kamera ayarları
        const cameraPresets = {
            anit: {          // Sütunlar, dikilitaşlar - küçük objeler
                height: 45,
                lonOffset: -0.0001,
                latOffset: 0.0007,
                pitch: -25
            },
            cesme: {         // Çeşmeler - küçük objeler
                height: 35,
                lonOffset: +0.0000,
                latOffset: 0.0005,
                pitch: -30
            },
            turbe: {         // Türbeler - orta boy
                height: 70,
                lonOffset: -0.0001,
                latOffset: 0.0012,
                pitch: -25
            },
            cami: {          // Camiler - büyük yapılar
                height: 120,
                lonOffset: -0.0004,
                latOffset: 0.0025,
                pitch: -20
            },
            kilise: {        // Kiliseler/Müzeler - büyük yapılar
                height: 130,
                lonOffset: -0.0004,
                latOffset: 0.0028,
                pitch: -20
            },
            saray: {         // Saraylar - çok büyük yapılar
                height: 180,
                lonOffset: -0.0006,
                latOffset: 0.0035,
                pitch: -18
            },
            diger: {         // Diğer - varsayılan
                height: 80,
                lonOffset: -0.0003,
                latOffset: 0.0018,
                pitch: -22
            }
        };

        const buildingType = asset.buildingType || 'diger';
        return cameraPresets[buildingType] || cameraPresets.diger;
    }

    /**
     * Kamerayı asset'e zoom at
     */
    function zoomToAsset(asset) {
        if (!asset.position) return;

        // Yapı tipine göre dinamik kamera ayarları al
        const cam = getCameraSettingsForAsset(asset);

        const destination = Cesium.Cartesian3.fromDegrees(
            asset.position.lon + cam.lonOffset,
            asset.position.lat + cam.latOffset,
            cam.height
        );

        CesiumViewer.getViewer().camera.flyTo({
            destination: destination,
            orientation: {
                heading: Cesium.Math.toRadians(180),
                pitch: Cesium.Math.toRadians(cam.pitch),
                roll: 0.0
            },
            duration: 1.5
        });
    }

    /**
     * Hakkında panelini aç/kapat
     */
    function toggleAboutPanel() {
        if (state.isAboutPanelOpen) {
            closeAboutPanel();
        } else {
            openAboutPanel();
        }
    }

    /**
     * Hakkında panelini aç
     */
    function openAboutPanel() {
        state.isAboutPanelOpen = true;
        elements.aboutPanel.classList.add('open');

        // Asset panel'i kapat
        closeAssetPanel();

        // Seçili asset'i temizle
        state.currentAssetId = null;

        // Location badge'i güncelle
        if (elements.locationText) {
            elements.locationText.textContent = 'Tarihi Yarımada - İstanbul';
        }

        // Panel açıkken haritayı sağa kaydır (panel 500px)
        // Böylece yarımada tam görünür
        const viewer = CesiumViewer.getViewer();
        if (viewer) {
            viewer.camera.flyTo({
                destination: Cesium.Cartesian3.fromDegrees(
                    28.9562 - 0.025,  // Sağa (doğuya) kaydır
                    40.9538,
                    7500
                ),
                orientation: {
                    heading: Cesium.Math.toRadians(0),
                    pitch: Cesium.Math.toRadians(-50),
                    roll: 0.0
                },
                duration: 2.0
            });
        }
    }

    /**
     * Hakkında panelini kapat
     */
    function closeAboutPanel() {
        state.isAboutPanelOpen = false;
        elements.aboutPanel.classList.remove('open');

        // Haritayı merkeze geri getir
        CesiumViewer.flyToHome();
    }

    /**
     * Loading status güncelle
     */
    function updateLoadingStatus(message) {
        if (elements.loaderStatus) {
            elements.loaderStatus.textContent = message;
        }
    }

    /**
     * Loading ekranını gizle
     */
    function hideLoadingScreen() {
        state.isLoading = false;
        setTimeout(() => {
            elements.loadingScreen.classList.add('hidden');
            elements.app.classList.remove('hidden');
        }, 500);
    }

    /**
     * API bağlantısını kontrol et
     */
    async function checkAPIConnection() {
        try {
            await API.healthCheck();
            updateConnectionStatus(true);
        } catch (error) {
            updateConnectionStatus(false);
        }
        
        API.onConnectionChange(updateConnectionStatus);
    }

    /**
     * Bağlantı durumunu güncelle
     */
    function updateConnectionStatus(isConnected) {
        const statusDot = document.querySelector('.status-dot');
        if (statusDot) {
            statusDot.classList.toggle('online', isConnected);
            statusDot.classList.toggle('offline', !isConnected);
        }
    }

    /**
     * Basemap değiştir
     */
    async function handleBasemapChange(basemapId) {
        if (state.currentBasemap === basemapId) return;

        // Update UI
        document.querySelectorAll('.basemap-option').forEach(option => {
            option.classList.toggle('active', option.dataset.basemap === basemapId);
        });

        // Change basemap in Cesium
        const success = await CesiumViewer.setBasemap(basemapId);

        if (success !== false) {
            state.currentBasemap = basemapId;
            console.log('Altlık harita değiştirildi:', basemapId);
        } else {
            // Revert UI on failure
            document.querySelectorAll('.basemap-option').forEach(option => {
                option.classList.toggle('active', option.dataset.basemap === state.currentBasemap);
            });
        }
    }

    /**
     * Katman aç/kapat
     */
    function handleLayerToggle(layerType, isVisible) {
        console.log(`Layer ${layerType} visibility:`, isVisible);

        switch (layerType) {
            case 'buildings':
                // Tüm bina modellerini göster/gizle
                Object.values(state.loadedTilesets).forEach(tileset => {
                    tileset.show = isVisible;
                });
                break;
            case 'terrain':
                CesiumViewer.setTerrain(isVisible);
                break;
            case 'labels':
                // Etiketleri göster/gizle (Cesium özelliği)
                if (CesiumViewer.getViewer()) {
                    CesiumViewer.getViewer().scene.globe.enableLighting = isVisible;
                }
                break;
            case 'borders':
                // Sınırları göster/gizle (özel uygulama gerekli)
                console.log('Borders toggle not yet implemented');
                break;
        }
    }

    /**
     * Modal aç
     */
    function openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('open');
        }
    }

    /**
     * Tüm modalleri kapat
     */
    function closeAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('open');
        });
    }

    /**
     * Home butonuna tıkla
     */
    function handleHomeClick() {
        showHomeView();
    }

    /**
     * Orbit modunu aç/kapat
     */
    function handleOrbitToggle() {
        // Seçili yapı yoksa uyarı ver
        if (!state.currentAssetId) {
            showToast('Önce bir yapı seçin', 'error');
            return;
        }

        toggleOrbitMode();
    }

    /**
     * Orbit modunu aç/kapat (ortak fonksiyon)
     */
    function toggleOrbitMode() {
        state.orbitLocked = !state.orbitLocked;

        if (state.orbitLocked) {
            // Seçili yapı bilgilerini al
            const asset = AssetsData.getAsset(state.currentAssetId);
            if (asset) {
                // Yapı tipine göre varsayılan orbit radius
                const radiusMap = {
                    anit: 25,      // Sütunlar, dikilitaşlar - küçük
                    cesme: 20,     // Çeşmeler - küçük
                    turbe: 35,     // Türbeler - orta
                    cami: 80,      // Camiler - büyük
                    kilise: 90,    // Kiliseler/Müzeler - büyük
                    saray: 150,    // Saraylar - çok büyük
                    diger: 50      // Diğer - varsayılan
                };
                const defaultRadius = radiusMap[asset.buildingType] || radiusMap.diger;

                // Fallback koordinatları hazırla
                const fallbackPosition = {
                    lon: asset.position?.lon || 28.9750,
                    lat: asset.position?.lat || 41.0100,
                    height: 0,
                    radius: defaultRadius
                };

                // Tileset varsa kullan, yoksa fallback koordinatlar
                let ionAssetId = null;
                if (asset.ionAssetIds && asset.ionAssetIds.length > 0) {
                    ionAssetId = asset.ionAssetIds[0].id;
                }

                CesiumViewer.orbitAroundTileset(ionAssetId, fallbackPosition);
            }
            // Butonları güncelle
            if (elements.btnOrbit) {
                elements.btnOrbit.classList.add('active');
            }
            if (elements.btnAssetOrbit) {
                elements.btnAssetOrbit.classList.add('active');
            }
        } else {
            CesiumViewer.unlockOrbit();
            if (elements.btnOrbit) {
                elements.btnOrbit.classList.remove('active');
            }
            if (elements.btnAssetOrbit) {
                elements.btnAssetOrbit.classList.remove('active');
            }
        }
    }

    /**
     * Asset View Controls - Orbit butonu (harita üzerinde)
     */
    function handleAssetOrbit() {
        if (!state.currentAssetId) return;
        toggleOrbitMode();
    }

    /**
     * Asset View Controls - Zoom/Odaklan butonu (harita üzerinde)
     */
    function handleAssetZoom() {
        if (!state.currentAssetId) return;

        // Orbit modunu kapat
        if (state.orbitLocked) {
            state.orbitLocked = false;
            CesiumViewer.unlockOrbit();
            if (elements.btnOrbit) elements.btnOrbit.classList.remove('active');
            if (elements.btnAssetOrbit) elements.btnAssetOrbit.classList.remove('active');
        }

        // Yapıya tekrar zoom yap
        const asset = AssetsData.getAsset(state.currentAssetId);
        if (asset) {
            zoomToAsset(asset);
        }
    }

    /**
     * Asset View Controls - Kapat butonu (harita üzerinde)
     */
    function handleAssetClose() {
        closeAssetPanel();
    }

    /**
     * Asset View Controls overlay'ini göster
     */
    function showAssetViewControls() {
        if (elements.assetViewControls) {
            elements.assetViewControls.classList.add('visible');
        }
    }

    /**
     * Asset View Controls overlay'ini gizle
     */
    function hideAssetViewControls() {
        if (elements.assetViewControls) {
            elements.assetViewControls.classList.remove('visible');
            // Orbit butonunun active durumunu da sıfırla
            if (elements.btnAssetOrbit) {
                elements.btnAssetOrbit.classList.remove('active');
            }
        }
    }

    /**
     * Yakınlaştır
     */
    function handleZoomIn() {
        CesiumViewer.zoomIn();
    }

    /**
     * Uzaklaştır
     */
    function handleZoomOut() {
        CesiumViewer.zoomOut();
    }

    /**
     * Tam ekran
     */
    function handleFullscreen() {
        CesiumViewer.toggleFullscreen();
    }

    /**
     * Point boyutu değişikliği
     */
    function handlePointSizeChange(size) {
        if (state.cesiumReady) {
            CesiumViewer.setPointSize(size);
        }
    }

    // ============================================
    // NOTES (Notlar) İşlevleri
    // ============================================

    /**
     * Karakter sayacını güncelle
     */
    function updateCharCount() {
        const count = elements.noteContent.value.length;
        elements.charCount.textContent = count;
        
        if (count > 450) {
            elements.charCount.parentElement.style.color = 'var(--color-warning)';
        } else {
            elements.charCount.parentElement.style.color = '';
        }
    }

    /**
     * Notu kaydet
     */
    async function handleSaveNote() {
        const title = elements.noteTitle.value.trim();
        const content = elements.noteContent.value.trim();
        const author = elements.noteAuthor.value.trim();
        
        if (!title) {
            showToast('Lütfen bir başlık girin', 'error');
            elements.noteTitle.focus();
            return;
        }
        
        if (!content) {
            showToast('Lütfen not içeriği girin', 'error');
            elements.noteContent.focus();
            return;
        }
        
        elements.btnSaveNote.disabled = true;
        elements.btnSaveNote.classList.add('saving');
        
        try {
            const noteText = title + '\n\n' + content;

            // Backend numeric ID kullan (string identifier değil)
            let numericAssetId = 1;
            if (state.currentAssetId) {
                const asset = AssetsData.getAsset(state.currentAssetId);
                if (asset && asset._backend && asset._backend.id) {
                    numericAssetId = asset._backend.id;
                }
            }

            const noteData = {
                asset_id: numericAssetId,
                user_identifier: author || 'Anonim Kullanıcı',
                note_text: noteText
            };

            await API.addNote(noteData);
            
            showToast('Notunuz başarıyla kaydedildi.', 'success');
            
            elements.noteTitle.value = '';
            elements.noteContent.value = '';
            elements.noteAuthor.value = '';
            updateCharCount();

            await loadNotes(state.currentAssetId);
            
        } catch (error) {
            console.error('Not kaydedilemedi:', error);
            showToast('Not kaydedilemedi. Lütfen tekrar deneyin.', 'error');
        } finally {
            elements.btnSaveNote.disabled = false;
            elements.btnSaveNote.classList.remove('saving');
        }
    }

    /**
     * Notları yükle
     */
    async function loadNotes(assetId = null) {
        if (elements.btnRefreshNotes) {
            elements.btnRefreshNotes.classList.add('spinning');
        }

        try {
            // Backend numeric ID kullan (string identifier değil)
            let numericAssetId = 1;
            const targetId = assetId || state.currentAssetId;

            if (targetId) {
                const asset = AssetsData.getAsset(targetId);
                if (asset && asset._backend && asset._backend.id) {
                    numericAssetId = asset._backend.id;
                }
            }

            const notes = await API.getNotes(numericAssetId);
            state.notes = notes || [];

            if (elements.notesCountNumber) {
                elements.notesCountNumber.textContent = state.notes.length;
            }

            renderNotes();

        } catch (error) {
            console.warn('Notlar yüklenemedi:', error);
            state.notes = [];
            renderNotes();
        } finally {
            if (elements.btnRefreshNotes) {
                elements.btnRefreshNotes.classList.remove('spinning');
            }
        }
    }

    /**
     * Notları render et
     */
    function renderNotes() {
        if (!elements.notesItems) return;
        
        if (state.notes.length === 0) {
            elements.notesItems.innerHTML = `
                <div class="notes-empty">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48">
                        <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
                        <polyline points="14 2 14 8 20 8"/>
                        <line x1="16" y1="13" x2="8" y2="13"/>
                        <line x1="16" y1="17" x2="8" y2="17"/>
                        <line x1="10" y1="9" x2="8" y2="9"/>
                    </svg>
                    <p>Henüz not eklenmemiş</p>
                    <span>Yukarıdaki formu kullanarak ilk notunuzu ekleyin!</span>
                </div>
            `;
            return;
        }
        
        const sortedNotes = [...state.notes].reverse();
        
        elements.notesItems.innerHTML = sortedNotes.map(note => {
            const noteText = note.note_text || '';
            const lines = noteText.split('\n');
            const title = lines[0] || 'Not';
            const content = lines.slice(1).join('\n').trim();
            
            return `
                <div class="note-card" data-note-id="${note.id}">
                    <div class="note-card-header">
                        <div class="note-card-title">${escapeHtml(title)}</div>
                    </div>
                    ${content ? `<div class="note-card-content">${escapeHtml(content)}</div>` : ''}
                    <div class="note-card-meta">
                        <span class="note-card-author">${escapeHtml(note.user_identifier || 'Anonim')}</span>
                        <span class="note-card-date">${formatDate(note.created_at)}</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    /**
     * Yılı formatla (M.Ö. / M.S.) - UI görüntüleme için
     */
    function formatYearDisplay(year) {
        if (!year || year === '-') return '-';
        // String ise ve özel format içeriyorsa doğrudan döndür
        if (typeof year === 'string') {
            // M.Ö., yüzyıl, tahmini gibi özel formatlar
            if (year.includes('M.Ö.') || year.includes('yüzyıl') || year.includes('tahmini')) {
                return year;
            }
        }
        // Sayı ise formatla
        const numYear = parseInt(year);
        if (isNaN(numYear)) return year;
        if (numYear < 0) {
            return `M.Ö. ${Math.abs(numYear)}`;
        }
        return numYear.toString();
    }

    /**
     * HTML escape
     */
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Tarihi formatla
     */
    function formatDate(dateString) {
        if (!dateString) return '';
        try {
            const date = new Date(dateString);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMs / 3600000);
            const diffDays = Math.floor(diffMs / 86400000);
            
            if (diffMins < 1) return 'Az önce';
            if (diffMins < 60) return `${diffMins} dk önce`;
            if (diffHours < 24) return `${diffHours} saat önce`;
            if (diffDays < 7) return `${diffDays} gün önce`;
            
            return date.toLocaleDateString('tr-TR', {
                day: 'numeric',
                month: 'short',
                year: 'numeric'
            });
        } catch {
            return '';
        }
    }

    /**
     * Toast mesajı göster
     */
    function showToast(message, type = 'success') {
        const existingToast = document.querySelector('.note-toast');
        if (existingToast) {
            existingToast.remove();
        }
        
        const toast = document.createElement('div');
        toast.className = `note-toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 400);
        }, 3000);
    }

    // Public API
    return {
        initialize,
        selectAsset,
        showHomeView
    };
})();

// DOM yüklendiğinde uygulamayı başlat
document.addEventListener('DOMContentLoaded', () => {
    App.initialize();
});

// Global erişim
window.App = App;

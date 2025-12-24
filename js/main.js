/**
 * Tarihi Yarımada CBS - Main Application
 * Ana uygulama kontrolcüsü
 */

const App = (function() {
    // Uygulama durumu
    const state = {
        currentView: 'cesium', // 'cesium' (tek görünüm)
        isPanelOpen: false,
        isBasemapPanelOpen: false,
        currentBasemap: 'satellite', // Varsayılan: uydu görüntüsü
        isLoading: true,
        cesiumReady: false,
        orbitLocked: false, // Orbit kilidi durumu
        currentYapiId: 1, // Varsayılan yapı ID (Molla Hüsrev Camii)
        notes: [], // Kayıtlı notlar
        interiorMode: false, // İç mekan modu aktif mi?
        loadedTilesets: {}, // Yüklenen tilesetler: { assetId: tileset }
        renderQuality: 'high' // Varsayılan render kalitesi
    };

    // DOM elementleri
    const elements = {};

    /**
     * Uygulamayı başlat
     */
    async function initialize() {
        console.log('Tarihi Yarımada CBS başlatılıyor...');
        
        // DOM elementlerini cache'le
        cacheElements();
        
        // Event listener'ları kur
        setupEventListeners();
        
        // API bağlantısını kontrol et
        checkAPIConnection();
        
        // Viewer'ları başlat
        await initializeViewers();
        
        // Loading ekranını kapat
        hideLoadingScreen();
        
        // Notları yükle
        loadNotes();
        
        console.log('Uygulama başarıyla başlatıldı');
    }

    /**
     * DOM elementlerini cache'le
     */
    function cacheElements() {
        elements.loadingScreen = document.getElementById('loading-screen');
        elements.app = document.getElementById('app');
        elements.loaderStatus = document.querySelector('.loader-status');
        
        // Containers
        elements.cesiumContainer = document.getElementById('cesium-container');
        elements.mainContent = document.querySelector('.main-content');
        
        // Navigation
        elements.navButtons = document.querySelectorAll('.nav-btn');
        
        // Side Panel
        elements.sidePanel = document.getElementById('side-panel');
        elements.panelClose = document.getElementById('panel-close');
        
        // Header buttons
        elements.btnBasemap = document.getElementById('btn-basemap');
        elements.btnLayers = document.getElementById('btn-layers');
        elements.btnInfo = document.getElementById('btn-info');
        elements.btnSettings = document.getElementById('btn-settings');
        
        // Basemap Panel
        elements.basemapPanel = document.getElementById('basemap-panel');
        elements.basemapClose = document.getElementById('basemap-close');
        elements.basemapItems = document.querySelectorAll('.basemap-item');
        
        // Floating controls
        elements.btnHome = document.getElementById('btn-home');
        elements.btnOrbit = document.getElementById('btn-orbit');
        elements.btnZoomIn = document.getElementById('btn-zoom-in');
        elements.btnZoomOut = document.getElementById('btn-zoom-out');
        elements.btnFullscreen = document.getElementById('btn-fullscreen');
        
        // Modals
        elements.infoModal = document.getElementById('info-modal');
        elements.settingsModal = document.getElementById('settings-modal');
        
        // Layer checkboxes
        elements.layerCheckboxes = document.querySelectorAll('.layer-item input');
        
        // Settings controls
        elements.renderQuality = document.getElementById('render-quality');
        elements.pointSize = document.getElementById('point-size');
        elements.showShadows = document.getElementById('show-shadows');
        elements.terrainEnabled = document.getElementById('terrain-enabled');
        
        // Notes elements
        elements.noteTitle = document.getElementById('note-title');
        elements.noteContent = document.getElementById('note-content');
        elements.noteAuthor = document.getElementById('note-author');
        elements.charCount = document.getElementById('char-count');
        elements.btnSaveNote = document.getElementById('btn-save-note');
        elements.btnRefreshNotes = document.getElementById('btn-refresh-notes');
        elements.notesCountNumber = document.getElementById('notes-count-number');
        elements.notesItems = document.getElementById('notes-items');
        
        // Interior Navigation elements
        elements.btnEnterInterior = document.getElementById('btn-enter-interior');
    }

    /**
     * Event listener'ları kur
     */
    function setupEventListeners() {
        // Navigation buttons
        elements.navButtons.forEach(btn => {
            btn.addEventListener('click', () => handleNavigation(btn.dataset.view));
        });
        
        // Header buttons
        elements.btnBasemap.addEventListener('click', toggleBasemapPanel);
        elements.btnLayers.addEventListener('click', toggleSidePanel);
        elements.btnInfo.addEventListener('click', () => openModal('info-modal'));
        elements.btnSettings.addEventListener('click', () => openModal('settings-modal'));
        
        // Basemap panel
        elements.basemapClose.addEventListener('click', closeBasemapPanel);
        elements.basemapItems.forEach(item => {
            item.addEventListener('click', () => handleBasemapChange(item.dataset.basemap));
        });
        
        // Panel close
        elements.panelClose.addEventListener('click', closeSidePanel);
        
        // Floating controls
        elements.btnHome.addEventListener('click', handleHomeClick);
        elements.btnOrbit.addEventListener('click', handleOrbitToggle);
        elements.btnZoomIn.addEventListener('click', handleZoomIn);
        elements.btnZoomOut.addEventListener('click', handleZoomOut);
        elements.btnFullscreen.addEventListener('click', handleFullscreen);
        
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
        
        // Layer checkboxes
        elements.layerCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                handleLayerToggle(e.target.dataset.layer, e.target.checked);
            });
        });
        
        
        // Settings
        if (elements.renderQuality) {
            elements.renderQuality.addEventListener('change', (e) => {
                handleQualityChange(e.target.value);
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
        
        // Keyboard shortcuts
        document.addEventListener('keydown', handleKeyboard);
        
        // Escape key to close modals/panel
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeAllModals();
                closeSidePanel();
                closeBasemapPanel();
            }
        });
        
        // Click outside to close basemap panel (ama side panel'i etkilemesin)
        document.addEventListener('click', (e) => {
            // Basemap panel kontrolü
            if (state.isBasemapPanelOpen && 
                !elements.basemapPanel.contains(e.target) && 
                !elements.btnBasemap.contains(e.target)) {
                closeBasemapPanel();
            }
        });
        
        // Input alanlarına focus olduğunda panel kapanmasını engelle
        document.querySelectorAll('.note-input, .note-textarea').forEach(input => {
            input.addEventListener('focus', (e) => {
                e.stopPropagation();
            });
            input.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        });
        
        // Notes event listeners
        if (elements.noteContent) {
            elements.noteContent.addEventListener('input', updateCharCount);
        }
        
        if (elements.btnSaveNote) {
            elements.btnSaveNote.addEventListener('click', handleSaveNote);
        }
        
        if (elements.btnRefreshNotes) {
            elements.btnRefreshNotes.addEventListener('click', loadNotes);
        }
        
        // Interior Navigation - İç Mekana Giriş Butonu
        if (elements.btnEnterInterior) {
            elements.btnEnterInterior.addEventListener('click', handleEnterInterior);
        }
    }

    /**
     * Viewer'ları başlat
     */
    async function initializeViewers() {
        updateLoadingStatus('Cesium Viewer hazırlanıyor...');
        
        try {
            // Cesium Viewer'ı başlat
            await CesiumViewer.initialize('cesiumViewer');
            state.cesiumReady = true;
            
            // FPS sayacını başlat
            CesiumViewer.startFPSCounter();
            
            // Render kalitesini yüksek olarak ayarla
            CesiumViewer.setQuality(state.renderQuality);
            
            // Molla Hüsrev Camii 3D modellerini yükle
            updateLoadingStatus('3D modeller yükleniyor...');

            // Dış cephe (Asset ID: 4270999)
            const exteriorTileset = await CesiumViewer.loadFromIonAssetId(4270999, { zoomTo: false });
            state.loadedTilesets['4270999'] = exteriorTileset;

            // İç mekan modelleri (Asset ID: 4271001 ve 4275532)
            const interior1Tileset = await CesiumViewer.loadFromIonAssetId(4271001, { zoomTo: false });
            state.loadedTilesets['4271001'] = interior1Tileset;

            const interior2Tileset = await CesiumViewer.loadFromIonAssetId(4275532, { zoomTo: false });
            state.loadedTilesets['4275532'] = interior2Tileset;

            // Şadırvan (Asset ID: 4277312)
            const sadirvanTileset = await CesiumViewer.loadFromIonAssetId(4277312, { zoomTo: false });
            state.loadedTilesets['4277312'] = sadirvanTileset;
            
            // Model etrafında orbit modunu aktifleştir
            updateLoadingStatus('Orbit modu ayarlanıyor...');
            CesiumViewer.enableOrbitAroundModel();
            
        } catch (error) {
            console.error('Cesium başlatılamadı:', error);
            updateLoadingStatus('Cesium yüklenirken hata oluştu');
        }
        
        updateLoadingStatus('Hazır!');
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
        
        // Bağlantı durumu değişikliklerini dinle
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
     * Loading durumunu güncelle
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
     * Navigasyon işleyicisi
     */
    function handleNavigation(view) {
        if (state.currentView === view) return;
        
        state.currentView = view;
        
        // Nav butonlarını güncelle
        elements.navButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === view);
        });
        
        // Cesium her zaman aktif (tek görünüm)
        elements.cesiumContainer.classList.add('active');
        
        // Location badge'i güncelle
        updateLocationBadge(view);
    }

    /**
     * Location badge'i güncelle
     */
    function updateLocationBadge(view) {
        const cesiumBadge = elements.cesiumContainer?.querySelector('.location-text');
        
        if (cesiumBadge) {
            if (state.interiorMode) {
                cesiumBadge.textContent = 'Molla Hüsrev Camii - İç Mekan Gezintisi';
            } else {
                cesiumBadge.textContent = 'Molla Hüsrev Camii - 3D Görünüm';
            }
        }
    }

    /**
     * Side panel toggle
     */
    function toggleSidePanel() {
        state.isPanelOpen = !state.isPanelOpen;
        elements.sidePanel.classList.toggle('open', state.isPanelOpen);
    }

    /**
     * Side panel kapat
     */
    function closeSidePanel() {
        state.isPanelOpen = false;
        elements.sidePanel.classList.remove('open');
    }

    /**
     * Basemap panel toggle
     */
    function toggleBasemapPanel() {
        state.isBasemapPanelOpen = !state.isBasemapPanelOpen;
        elements.basemapPanel.classList.toggle('open', state.isBasemapPanelOpen);
        
        // Diğer panelleri kapat
        if (state.isBasemapPanelOpen) {
            closeSidePanel();
        }
    }

    /**
     * Basemap panel kapat
     */
    function closeBasemapPanel() {
        state.isBasemapPanelOpen = false;
        elements.basemapPanel.classList.remove('open');
    }

    /**
     * Altlık harita değiştir
     */
    async function handleBasemapChange(basemapId) {
        if (state.currentBasemap === basemapId) return;
        
        // UI'ı hemen güncelle (yükleniyor durumu)
        elements.basemapItems.forEach(item => {
            item.classList.toggle('active', item.dataset.basemap === basemapId);
        });
        
        // Cesium viewer'da altlık haritayı değiştir (async olabilir)
        const success = await CesiumViewer.setBasemap(basemapId);
        
        if (success !== false) {
            state.currentBasemap = basemapId;
            console.log('Altlık harita değiştirildi:', basemapId);
        } else {
            // Başarısız olursa eski seçimi geri al
            elements.basemapItems.forEach(item => {
                item.classList.toggle('active', item.dataset.basemap === state.currentBasemap);
            });
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
     * Home butonuna tıklama
     */
    function handleHomeClick() {
        if (state.interiorMode && typeof InteriorNavigation !== 'undefined') {
            // İç mekan modundayken girişe git
            InteriorNavigation.goToEntrance();
        } else {
            // Normal modda ana görünüme dön
            CesiumViewer.flyToHome();
        }
    }

    /**
     * Orbit modunu aç/kapat
     */
    function handleOrbitToggle() {
        if (state.currentView === 'cesium' || state.currentView === 'split') {
            state.orbitLocked = !state.orbitLocked;
            
            if (state.orbitLocked) {
                CesiumViewer.lockOrbitToModel();
                elements.btnOrbit.classList.add('active');
                elements.btnOrbit.title = 'Orbit Kilidini Kaldır (Serbest Hareket)';
            } else {
                CesiumViewer.unlockOrbit();
                elements.btnOrbit.classList.remove('active');
                elements.btnOrbit.title = 'Model Etrafında Dön (Orbit Kilitle)';
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
     * Katman toggle
     */
    function handleLayerToggle(layerId, visible) {
        console.log(`Katman ${layerId}: ${visible ? 'açık' : 'kapalı'}`);
        
        // Asset ID'yi bul
        const checkbox = document.querySelector(`input[data-layer="${layerId}"]`);
        const assetId = checkbox?.dataset.assetId;
        
        if (assetId && state.loadedTilesets[assetId]) {
            state.loadedTilesets[assetId].show = visible;
            console.log(`Tileset ${assetId} görünürlük: ${visible}`);
        } else {
            // Fallback: CesiumViewer'ın setLayerVisibility'sini kullan
            CesiumViewer.setLayerVisibility(layerId, visible);
        }
    }

    // ============================================
    // NOTLAR (Notes) İşlevleri
    // ============================================

    /**
     * Karakter sayacını güncelle
     */
    function updateCharCount() {
        const count = elements.noteContent.value.length;
        elements.charCount.textContent = count;
        
        // 450'den fazla karakterde uyarı rengi
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
        
        // Validasyon
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
        
        // Kaydetme durumunu göster
        elements.btnSaveNote.disabled = true;
        elements.btnSaveNote.classList.add('saving');
        elements.btnSaveNote.innerHTML = `
            <svg class="spinning" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                <polyline points="23 4 23 10 17 10"/>
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            Kaydediliyor...
        `;
        
        try {
            // Kamera pozisyonunu al (3D konum için)
            let x = 0, y = 0, z = 0;
            if (state.cesiumReady) {
                const viewer = CesiumViewer.getViewer();
                if (viewer && viewer.camera) {
                    const pos = viewer.camera.positionCartographic;
                    x = Cesium.Math.toDegrees(pos.longitude);
                    y = Cesium.Math.toDegrees(pos.latitude);
                    z = pos.height;
                }
            }
            
            // API'ye gönder
            const noteData = {
                yapi_id: state.currentYapiId,
                baslik: title,
                aciklama: content,
                x: x,
                y: y,
                z: z,
                olusturan: author || 'Anonim Kullanıcı'
            };
            
            await API.addNote(noteData);
            
            // Başarılı
            showToast('Notunuz başarıyla kaydedildi! ✨', 'success');
            
            // Formu temizle
            elements.noteTitle.value = '';
            elements.noteContent.value = '';
            elements.noteAuthor.value = '';
            updateCharCount();
            
            // Notları yeniden yükle
            await loadNotes();
            
        } catch (error) {
            console.error('Not kaydedilemedi:', error);
            showToast('Not kaydedilemedi. Lütfen tekrar deneyin.', 'error');
        } finally {
            // Butonu eski haline getir
            elements.btnSaveNote.disabled = false;
            elements.btnSaveNote.classList.remove('saving');
            elements.btnSaveNote.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                    <polyline points="17 21 17 13 7 13 7 21"/>
                    <polyline points="7 3 7 8 15 8"/>
                </svg>
                Notu Kaydet
            `;
        }
    }

    /**
     * Notları yükle
     */
    async function loadNotes() {
        // Yenileme butonuna animasyon ekle
        if (elements.btnRefreshNotes) {
            elements.btnRefreshNotes.classList.add('spinning');
        }
        
        try {
            const notes = await API.getNotes(state.currentYapiId);
            state.notes = notes || [];
            
            // Sayıyı güncelle
            if (elements.notesCountNumber) {
                elements.notesCountNumber.textContent = state.notes.length;
            }
            
            // Notları render et
            renderNotes();
            
        } catch (error) {
            console.warn('Notlar yüklenemedi:', error);
            state.notes = [];
            renderNotes();
        } finally {
            // Animasyonu kaldır
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
            // Boş durum
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
        
        // Notları ters sırayla göster (en yeni en üstte)
        const sortedNotes = [...state.notes].reverse();
        
        elements.notesItems.innerHTML = sortedNotes.map(note => `
            <div class="note-card" data-note-id="${note.id}">
                <div class="note-card-header">
                    <div class="note-card-title">${escapeHtml(note.baslik)}</div>
                </div>
                ${note.aciklama ? `<div class="note-card-content">${escapeHtml(note.aciklama)}</div>` : ''}
                <div class="note-card-meta">
                    <span class="note-card-author">${escapeHtml(note.olusturan || 'Anonim')}</span>
                    <span class="note-card-date">${formatDate(note.olusturulma_tarihi)}</span>
                </div>
            </div>
        `).join('');
    }

    /**
     * HTML karakterlerini escape et (XSS koruması)
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
        // Mevcut toast varsa kaldır
        const existingToast = document.querySelector('.note-toast');
        if (existingToast) {
            existingToast.remove();
        }
        
        // Yeni toast oluştur
        const toast = document.createElement('div');
        toast.className = `note-toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        // Animasyonla göster
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        // 3 saniye sonra kaldır
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 400);
        }, 3000);
    }

    // ============================================
    // İÇ MEKAN NAVİGASYON İşlevleri
    // ============================================

    /**
     * İç mekana giriş
     */
    async function handleEnterInterior() {
        if (!state.cesiumReady) {
            showToast('Cesium Viewer henüz hazır değil', 'error');
            return;
        }

        // Interior Navigation modülünü başlat (eğer yoksa)
        if (typeof InteriorNavigation !== 'undefined') {
            const viewer = CesiumViewer.getViewer();
            
            // Modülü başlat
            if (!InteriorNavigation.isInsideMode()) {
                InteriorNavigation.initialize(viewer);
            }
            
            // İç mekan moduna gir
            await InteriorNavigation.enterInterior(state.currentYapiId, state.interiorIonAssetId);
            
            state.interiorMode = true;
            
            // Giriş butonunu gizle
            if (elements.btnEnterInterior) {
                elements.btnEnterInterior.classList.add('hidden');
            }
            
            // Location badge güncelle
            const badge = document.querySelector('.viewer-overlay .location-text');
            if (badge) {
                badge.textContent = 'Molla Hüsrev Camii - İç Mekan Gezintisi';
            }
            
            showToast('İç mekan moduna geçildi. İyi gezintiler! 🏛️', 'success');
        } else {
            console.warn('InteriorNavigation modülü yüklenmedi');
            showToast('İç mekan modülü yüklenemedi', 'error');
        }
    }

    /**
     * İç mekandan çıkış (public API için)
     */
    function handleExitInterior() {
        state.interiorMode = false;
        
        // Giriş butonunu göster
        if (elements.btnEnterInterior) {
            elements.btnEnterInterior.classList.remove('hidden');
            elements.btnEnterInterior.style.display = '';
        }
        
        // Location badge güncelle
        updateLocationBadge('cesium');
        
        console.log('İç mekan modundan çıkıldı, buton tekrar gösterildi');
    }

    /**
     * Kalite değişikliği
     */
    function handleQualityChange(quality) {
        state.renderQuality = quality;
        CesiumViewer.setQuality(quality);
    }

    /**
     * Point boyutu değişikliği
     */
    function handlePointSizeChange(size) {
        // Cesium viewer için (3D Tiles point cloud desteği)
        if (state.cesiumReady) {
            CesiumViewer.setPointSize(size);
        }
    }

    /**
     * Klavye kısayolları
     */
    function handleKeyboard(e) {
        // Input alanlarında yazarken kısayolları devre dışı bırak
        const activeElement = document.activeElement;
        const isTyping = activeElement && (
            activeElement.tagName === 'INPUT' || 
            activeElement.tagName === 'TEXTAREA' ||
            activeElement.isContentEditable
        );
        
        if (isTyping) {
            return; // Yazı yazılıyorsa kısayolları çalıştırma
        }
        
        // Ctrl+H: Ana görünüme dön
        if (e.ctrlKey && e.key === 'h') {
            e.preventDefault();
            handleHomeClick();
        }
        // Ctrl+I: İç mekan moduna gir/çık
        if (e.ctrlKey && e.key === 'i') {
            e.preventDefault();
            if (state.interiorMode) {
                handleExitInterior();
            } else {
                handleEnterInterior();
            }
        }
        // Ctrl+L: Katmanlar panelini aç/kapat
        if (e.ctrlKey && e.key === 'l') {
            e.preventDefault();
            toggleSidePanel();
        }
    }

    /**
     * Tileset URL ile yükle
     */
    async function loadTileset(url) {
        try {
            await CesiumViewer.loadTileset(url);
            console.log('Tileset yüklendi:', url);
        } catch (error) {
            console.error('Tileset yüklenemedi:', error);
        }
    }

    /**
     * Ion Asset ID ile yükle
     */
    async function loadFromIonAssetId(assetId, options = {}) {
        try {
            const tileset = await CesiumViewer.loadFromIonAssetId(assetId, options);
            state.loadedTilesets[assetId.toString()] = tileset;
            console.log('Ion Asset yüklendi:', assetId);
            return tileset;
        } catch (error) {
            console.error('Ion Asset yüklenemedi:', error);
        }
    }

    /**
     * Belirli bir tileset'in görünürlüğünü ayarla
     */
    function setTilesetVisibility(assetId, visible) {
        const tileset = state.loadedTilesets[assetId.toString()];
        if (tileset) {
            tileset.show = visible;
        }
    }

    // Public API
    return {
        initialize,
        loadTileset,
        loadFromIonAssetId,
        setTilesetVisibility,
        
        // State
        getState: () => ({ ...state }),
        getLoadedTilesets: () => ({ ...state.loadedTilesets }),
        
        // Navigation
        switchView: handleNavigation,
        
        // Basemap
        setBasemap: handleBasemapChange,
        toggleBasemapPanel,
        
        // Modals
        openModal,
        closeAllModals,
        
        // Interior Navigation
        enterInterior: handleEnterInterior,
        exitInterior: handleExitInterior,
        isInteriorMode: () => state.interiorMode
    };
})();

// DOM yüklendiğinde uygulamayı başlat
document.addEventListener('DOMContentLoaded', () => {
    App.initialize();
});

// Global erişim için
window.App = App;


/**
 * Tarihi Yarımada CBS - Cesium Viewer Module
 * 3D Tiles ve dış cephe görselleştirmesi
 */

const CesiumViewer = (function() {
    // Cesium Ion Access Token - Backend'den yüklenir
    // Token artık hardcoded değil, initializeToken() ile yükleniyor
    let tokenLoaded = false;

    // Viewer instance
    let viewer = null;
    let currentTileset = null;
    let contextTileset = null;

    // Molla Hüsrev Camii koordinatları (Fatih, İstanbul)
    const MOLLA_HUSREV_LOCATION = {
        longitude: 28.9593,
        latitude: 41.0135,
        height: 100
    };

    // Default kamera pozisyonu
    const DEFAULT_CAMERA = {
        destination: Cesium.Cartesian3.fromDegrees(
            MOLLA_HUSREV_LOCATION.longitude,
            MOLLA_HUSREV_LOCATION.latitude - 0.002,
            MOLLA_HUSREV_LOCATION.height + 150
        ),
        orientation: {
            heading: Cesium.Math.toRadians(0),
            pitch: Cesium.Math.toRadians(-35),
            roll: 0.0
        }
    };

    // Ayarlar
    const settings = {
        shadows: true,
        terrainEnabled: false, // Terrain kapalı - model konumu değişmesin
        globeVisible: true, // Altlık harita görünürlüğü
        quality: 'medium',
        currentBasemap: 'satellite', // Varsayılan olarak uydu görüntüsü
        pointSize: 5 // Point cloud nokta boyutu
    };

    // Altlık harita sağlayıcıları
    const basemapProviders = {
        // Cesium Ion World Imagery - En iyi uydu görüntüsü (Varsayılan)
        satellite: async () => {
            try {
                return await Cesium.IonImageryProvider.fromAssetId(2);
            } catch (e) {
                console.warn('Cesium Ion Imagery yüklenemedi, ESRI kullanılıyor');
                return new Cesium.ArcGisMapServerImageryProvider({
                    url: 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'
                });
            }
        },
        
        // OpenStreetMap - Sokak haritası
        osm: () => new Cesium.OpenStreetMapImageryProvider({
            url: 'https://tile.openstreetmap.org/'
        }),
        
        // OpenTopoMap - Topografik harita
        openTopo: () => new Cesium.OpenStreetMapImageryProvider({
            url: 'https://tile.opentopomap.org/'
        }),
        
        // Stamen Terrain - Topografik arazi
        stamenTerrain: () => new Cesium.OpenStreetMapImageryProvider({
            url: 'https://tiles.stadiamaps.com/tiles/stamen_terrain/'
        }),
        
        // CartoDB Positron - Açık minimal
        cartoPositron: () => new Cesium.OpenStreetMapImageryProvider({
            url: 'https://basemaps.cartocdn.com/light_all/'
        }),
        
        // CartoDB Dark Matter - Koyu tema
        cartoDark: () => new Cesium.OpenStreetMapImageryProvider({
            url: 'https://basemaps.cartocdn.com/dark_all/'
        }),
        
        // CartoDB Voyager - Renkli detaylı
        cartoVoyager: () => new Cesium.OpenStreetMapImageryProvider({
            url: 'https://basemaps.cartocdn.com/rastertiles/voyager/'
        })
    };

    /**
     * Backend'den Cesium Ion Access Token'ı yükle
     * @param {string} apiBaseUrl - Backend API base URL (opsiyonel)
     */
    async function initializeToken(apiBaseUrl = '') {
        if (tokenLoaded) {
            console.log('Cesium token zaten yüklü');
            return true;
        }

        try {
            // Backend API'den token al
            const response = await fetch(`${apiBaseUrl}/api/cesium-config`);
            
            if (!response.ok) {
                throw new Error(`Token yüklenemedi: ${response.status}`);
            }
            
            const config = await response.json();
            
            if (!config.accessToken) {
                throw new Error('Token response içinde accessToken bulunamadı');
            }
            
            // Cesium Ion token'ı ayarla
            Cesium.Ion.defaultAccessToken = config.accessToken;
            tokenLoaded = true;
            
            console.log('Cesium Ion token başarıyla yüklendi');
            return true;
            
        } catch (error) {
            console.error('Cesium token yüklenirken hata:', error);
            throw error;
        }
    }

    /**
     * API Base URL'i otomatik tespit et
     */
    function getApiBaseUrl() {
        // Development modunda (Live Server vb.) localhost:8000 kullan
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            if (window.location.port !== '8000') {
                return 'http://localhost:8000';
            }
        }
        // Production: aynı origin
        return window.location.origin;
    }

    /**
     * Cesium Viewer'ı başlat
     * @param {string} containerId - Viewer container element ID
     * @param {object} options - Başlatma seçenekleri
     * @param {string} options.apiBaseUrl - Backend API base URL (opsiyonel, otomatik tespit edilir)
     */
    async function initialize(containerId, options = {}) {
        if (viewer) {
            console.warn('Cesium Viewer zaten başlatılmış');
            return viewer;
        }

        // Backend API URL - otomatik tespit veya manuel
        const apiBaseUrl = options.apiBaseUrl || getApiBaseUrl();

        try {
            // Önce token'ı backend'den yükle
            await initializeToken(apiBaseUrl);

            // Viewer oluştur
            viewer = new Cesium.Viewer(containerId, {
                // Temel ayarlar
                animation: false,
                baseLayerPicker: false,
                fullscreenButton: false,
                vrButton: false,
                geocoder: false,
                homeButton: false,
                infoBox: true,
                sceneModePicker: false,
                selectionIndicator: true,
                timeline: false,
                navigationHelpButton: false,
                navigationInstructionsInitiallyVisible: false,
                
                // Performance
                requestRenderMode: true,
                maximumRenderTimeChange: Infinity,
                
                // Shadows
                shadows: settings.shadows,
                
                // Scene
                skyAtmosphere: new Cesium.SkyAtmosphere()
            });
            
            // Altlık haritayı ekle - Uydu görüntüsü varsayılan
            viewer.imageryLayers.removeAll();
            try {
                // Cesium Ion World Imagery (en kaliteli uydu görüntüsü)
                const satelliteImagery = await Cesium.IonImageryProvider.fromAssetId(2);
                viewer.imageryLayers.addImageryProvider(satelliteImagery);
                console.log('Cesium Ion Uydu görüntüsü yüklendi');
            } catch (e) {
                console.warn('Cesium Ion Imagery yüklenemedi, ESRI kullanılıyor:', e);
                // Fallback: ESRI World Imagery
                viewer.imageryLayers.addImageryProvider(
                    new Cesium.ArcGisMapServerImageryProvider({
                        url: 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'
                    })
                );
            }
            
            // Terrain kullanmıyoruz - model konumu sabit kalsın
            // Sadece düz ellipsoid (küre) kullanılıyor
            viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
            viewer.scene.globe.depthTestAgainstTerrain = false;

            // Scene ayarları
            configureScene();
            
            // Zoom sınırlarını ayarla - Sınırsız uzaklaşma
            const controller = viewer.scene.screenSpaceCameraController;
            controller.minimumZoomDistance = 1; // 1 metre minimum
            controller.maximumZoomDistance = 50000000; // 50.000 km maksimum (dünya görünümü için)

            // Kamerayı başlangıç pozisyonuna getir
            flyToHome();

            // Event listeners
            setupEventListeners();

            console.log('Cesium Viewer başarıyla başlatıldı');
            return viewer;

        } catch (error) {
            console.error('Cesium Viewer başlatılamadı:', error);
            throw error;
        }
    }

    /**
     * Scene ayarlarını yapılandır
     */
    function configureScene() {
        const scene = viewer.scene;
        
        // Globe ayarları
        scene.globe.enableLighting = true;
        // depthTestAgainstTerrain false olmalı, aksi halde 3D modeller terrain altında kalır
        scene.globe.depthTestAgainstTerrain = false;
        
        // Atmosphere
        scene.skyAtmosphere.hueShift = 0.0;
        scene.skyAtmosphere.saturationShift = 0.0;
        scene.skyAtmosphere.brightnessShift = 0.0;
        
        // Fog
        scene.fog.enabled = true;
        scene.fog.density = 0.0002;
        
        // Post-processing
        if (settings.quality === 'high' || settings.quality === 'ultra') {
            scene.postProcessStages.fxaa.enabled = true;
        }
        
        // Gölge ayarları
        if (settings.shadows) {
            viewer.shadowMap.enabled = true;
            viewer.shadowMap.softShadows = true;
            viewer.shadowMap.size = settings.quality === 'ultra' ? 4096 : 2048;
        }
    }

    /**
     * Event listener'ları kur
     */
    function setupEventListeners() {
        // Kamera hareket ettiğinde koordinatları güncelle
        viewer.camera.moveEnd.addEventListener(updateCoordinates);
        
        // Tıklama eventi
        const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
        
        handler.setInputAction(function(movement) {
            const pickedFeature = viewer.scene.pick(movement.position);
            if (Cesium.defined(pickedFeature)) {
                handleFeatureClick(pickedFeature);
            }
        }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
        
        // Mouse hareket eventi (hover)
        handler.setInputAction(function(movement) {
            const pickedFeature = viewer.scene.pick(movement.endPosition);
            handleFeatureHover(pickedFeature);
        }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);
    }

    /**
     * Koordinatları güncelle
     */
    function updateCoordinates() {
        const cameraPosition = viewer.camera.positionCartographic;
        const longitude = Cesium.Math.toDegrees(cameraPosition.longitude).toFixed(4);
        const latitude = Cesium.Math.toDegrees(cameraPosition.latitude).toFixed(4);
        
        const coordsElement = document.getElementById('coordinates');
        if (coordsElement) {
            coordsElement.textContent = `${latitude}° N, ${longitude}° E`;
        }
    }

    /**
     * Feature tıklama işleyicisi
     */
    function handleFeatureClick(feature) {
        if (feature && feature.primitive && feature.primitive.isCesium3DTileset) {
            console.log('3D Tile tıklandı:', feature);
            
            // Feature properties'i göster
            if (feature.getProperty) {
                const properties = {};
                const propertyNames = feature.getPropertyNames();
                propertyNames.forEach(name => {
                    properties[name] = feature.getProperty(name);
                });
                console.log('Özellikler:', properties);
            }
        }
    }

    /**
     * Feature hover işleyicisi
     */
    function handleFeatureHover(feature) {
        if (Cesium.defined(feature) && feature.primitive && feature.primitive.isCesium3DTileset) {
            document.body.style.cursor = 'pointer';
        } else {
            document.body.style.cursor = 'default';
        }
    }

    /**
     * Cesium Ion Asset ID ile 3D Tileset yükle
     * @param {number} assetId - Cesium Ion Asset ID (ör: 2866823)
     * @param {object} options - Yükleme seçenekleri
     */
    async function loadFromIonAssetId(assetId, options = {}) {
        if (!viewer) {
            throw new Error('Viewer başlatılmamış');
        }

        try {
            console.log('Cesium Ion Asset yükleniyor, ID:', assetId);
            
            const tileset = await Cesium.Cesium3DTileset.fromIonAssetId(assetId, {
                maximumScreenSpaceError: options.quality === 'ultra' ? 1 : 
                                         options.quality === 'high' ? 4 : 
                                         options.quality === 'medium' ? 8 : 16,
                maximumMemoryUsage: 512,
                dynamicScreenSpaceError: true,
                dynamicScreenSpaceErrorDensity: 0.00278,
                dynamicScreenSpaceErrorFactor: 4.0,
                ...options
            });

            viewer.scene.primitives.add(tileset);
            
            // Modelin her zaman görünür olmasını sağla
            tileset.show = true;
            
            // Tileset yüklendiğinde kamerası yakınlaştır
            if (options.zoomTo !== false) {
                await viewer.zoomTo(tileset);
            }

            currentTileset = tileset;
            console.log('Cesium Ion Asset başarıyla yüklendi, ID:', assetId);
            
            return tileset;

        } catch (error) {
            console.error('Cesium Ion Asset yüklenemedi:', error);
            throw error;
        }
    }

    /**
     * 3D Tileset yükle
     */
    async function loadTileset(url, options = {}) {
        if (!viewer) {
            throw new Error('Viewer başlatılmamış');
        }

        try {
            const tileset = await Cesium.Cesium3DTileset.fromUrl(url, {
                maximumScreenSpaceError: options.quality === 'ultra' ? 1 : 
                                         options.quality === 'high' ? 4 : 
                                         options.quality === 'medium' ? 8 : 16,
                maximumMemoryUsage: 512,
                dynamicScreenSpaceError: true,
                dynamicScreenSpaceErrorDensity: 0.00278,
                dynamicScreenSpaceErrorFactor: 4.0,
                ...options
            });

            viewer.scene.primitives.add(tileset);
            
            // Tileset yüklendiğinde kamerası yakınlaştır
            if (options.zoomTo !== false) {
                await viewer.zoomTo(tileset);
            }

            currentTileset = tileset;
            console.log('3D Tileset yüklendi:', url);
            
            return tileset;

        } catch (error) {
            console.error('3D Tileset yüklenemedi:', error);
            throw error;
        }
    }

    /**
     * LoD0 Context modeli yükle
     */
    async function loadContextModel(url) {
        try {
            contextTileset = await loadTileset(url, {
                zoomTo: false,
                maximumScreenSpaceError: 32
            });
            return contextTileset;
        } catch (error) {
            console.error('Context model yüklenemedi:', error);
            throw error;
        }
    }

    /**
     * Demo tileset yükle (Cesium OSM Buildings)
     */
    async function loadDemoBuildings() {
        try {
            // Cesium OSM Buildings (async API)
            const osmBuildingsTileset = await Cesium.createOsmBuildingsAsync();
            viewer.scene.primitives.add(osmBuildingsTileset);
            
            console.log('Demo binalar yüklendi');
            return osmBuildingsTileset;
        } catch (error) {
            console.warn('Demo binalar yüklenemedi (Cesium Ion token gerekebilir):', error);
            return null;
        }
    }

    /**
     * Başlangıç görünümüne dön
     */
    function flyToHome(duration = 2.0) {
        viewer.camera.flyTo({
            ...DEFAULT_CAMERA,
            duration: duration
        });
    }

    /**
     * Belirli bir konuma uç
     */
    function flyTo(longitude, latitude, height = 200, duration = 2.0) {
        viewer.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(longitude, latitude, height),
            orientation: {
                heading: 0,
                pitch: Cesium.Math.toRadians(-45),
                roll: 0
            },
            duration: duration
        });
    }

    /**
     * Tileset'e uç
     */
    function flyToTileset(tileset, duration = 2.0) {
        if (tileset) {
            viewer.flyTo(tileset, { duration: duration });
        }
    }

    /**
     * Model etrafında orbit modunu aktifleştir
     * Kamerayı modelin merkezine kilitler ve etrafında döndürme imkanı sağlar
     */
    function enableOrbitAroundModel() {
        if (!currentTileset) {
            console.warn('Tileset yüklenmemiş, orbit modu aktifleştirilemiyor');
            return;
        }

        // Tileset'in bounding sphere'ini al
        const boundingSphere = currentTileset.boundingSphere;
        if (!boundingSphere) {
            console.warn('Tileset bounding sphere bulunamadı');
            return;
        }

        const center = boundingSphere.center;
        const radius = boundingSphere.radius;

        // Kamera kontrolcüsünü ayarla - Orbit modu için
        const controller = viewer.scene.screenSpaceCameraController;
        
        // Zoom sınırlarını geniş tut - istediğin kadar uzaklaşabilirsin
        controller.minimumZoomDistance = 1; // 1 metre minimum
        controller.maximumZoomDistance = 50000000; // 50.000 km maksimum
        
        // Daha hassas kontroller
        controller.enableRotate = true;
        controller.enableTilt = true;
        controller.enableZoom = true;
        controller.enableLook = true;
        
        // Orbit davranışını iyileştir
        controller.inertiaSpin = 0.9;
        controller.inertiaTranslate = 0.9;
        controller.inertiaZoom = 0.8;

        // Kamerayı modelin merkezine odakla
        const heading = Cesium.Math.toRadians(45);
        const pitch = Cesium.Math.toRadians(-30);
        const range = radius * 2.5;

        viewer.camera.lookAt(
            center,
            new Cesium.HeadingPitchRange(heading, pitch, range)
        );

        // lookAt kilitlemesini kaldır ama merkez etrafında orbit için ayarı koru
        viewer.camera.lookAtTransform(Cesium.Matrix4.IDENTITY);

        console.log('Orbit modu aktifleştirildi - Model merkezine odaklandı');
    }

    /**
     * Model etrafında orbit - merkeze kilitle
     * Bu mod aktifken kamera sadece model etrafında döner
     */
    function lockOrbitToModel() {
        if (!currentTileset) {
            console.warn('Tileset yüklenmemiş');
            return;
        }

        const boundingSphere = currentTileset.boundingSphere;
        if (!boundingSphere) return;

        const center = boundingSphere.center;
        const radius = boundingSphere.radius;

        // Transform matrisini oluştur
        const transform = Cesium.Transforms.eastNorthUpToFixedFrame(center);

        // Kamerayı bu transform'a kilitle
        viewer.camera.lookAtTransform(
            transform,
            new Cesium.HeadingPitchRange(
                viewer.camera.heading,
                viewer.camera.pitch,
                radius * 2.5
            )
        );

        console.log('Kamera modele kilitlendi - Orbit modu aktif');
    }

    /**
     * Orbit kilidini kaldır - Serbest hareket
     */
    function unlockOrbit() {
        viewer.camera.lookAtTransform(Cesium.Matrix4.IDENTITY);
        console.log('Orbit kilidi kaldırıldı - Serbest hareket');
    }

    /**
     * Yakınlaştır
     */
    function zoomIn() {
        viewer.camera.zoomIn(viewer.camera.positionCartographic.height * 0.3);
    }

    /**
     * Uzaklaştır
     */
    function zoomOut() {
        viewer.camera.zoomOut(viewer.camera.positionCartographic.height * 0.3);
    }

    /**
     * Tam ekran modu
     */
    function toggleFullscreen() {
        const container = viewer.container;
        if (!document.fullscreenElement) {
            container.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    }

    /**
     * Gölgeleri aç/kapat
     */
    function setShadows(enabled) {
        settings.shadows = enabled;
        viewer.shadows = enabled;
        viewer.shadowMap.enabled = enabled;
    }

    /**
     * Altlık haritayı (globe/imagery) aç/kapat
     * Bu fonksiyon artık terrain yerine globe görünürlüğünü kontrol ediyor
     */
    function setTerrain(enabled) {
        settings.globeVisible = enabled;
        
        // Globe'u (altlık harita dahil) göster/gizle
        viewer.scene.globe.show = enabled;
        
        // Sky atmosphere'i de kontrol et
        if (viewer.scene.skyAtmosphere) {
            viewer.scene.skyAtmosphere.show = enabled;
        }
        
        // Modelin her zaman görünür kalmasını sağla
        if (currentTileset) {
            currentTileset.show = true;
        }
        
        console.log('Altlık harita:', enabled ? 'görünür' : 'gizli');
    }

    /**
     * Altlık haritayı değiştir
     */
    async function setBasemap(basemapId) {
        if (!basemapProviders[basemapId]) {
            console.error('Geçersiz altlık harita:', basemapId);
            return false;
        }

        try {
            // Mevcut imagery katmanlarını kaldır
            viewer.imageryLayers.removeAll();
            
            // Yeni altlık haritayı ekle (async olabilir)
            const providerResult = basemapProviders[basemapId]();
            
            // Promise kontrolü - async provider'lar için
            const imageryProvider = providerResult instanceof Promise 
                ? await providerResult 
                : providerResult;
            
            viewer.imageryLayers.addImageryProvider(imageryProvider);
            
            settings.currentBasemap = basemapId;
            console.log('Altlık harita değiştirildi:', basemapId);
            
            return true;
        } catch (error) {
            console.error('Altlık harita yüklenemedi:', error);
            // Hata durumunda OSM'e geri dön
            const fallback = basemapProviders['osm']();
            viewer.imageryLayers.addImageryProvider(fallback);
            return false;
        }
    }

    /**
     * Mevcut altlık harita listesini döndür
     */
    function getBasemapList() {
        return [
            // Uydu Görüntüsü
            { id: 'satellite', name: 'Uydu Görüntüsü', icon: '🛰️', category: 'satellite' },
            
            // Sokak Haritaları
            { id: 'osm', name: 'OpenStreetMap', icon: '🗺️', category: 'street' },
            { id: 'cartoVoyager', name: 'CartoDB Voyager', icon: '🛣️', category: 'street' },
            
            // Topografik
            { id: 'openTopo', name: 'OpenTopoMap', icon: '⛰️', category: 'terrain' },
            { id: 'stamenTerrain', name: 'Stamen Arazi', icon: '🏔️', category: 'terrain' },
            
            // Minimal
            { id: 'cartoPositron', name: 'CartoDB Açık', icon: '⬜', category: 'minimal' },
            { id: 'cartoDark', name: 'CartoDB Koyu', icon: '⬛', category: 'minimal' }
        ];
    }

    /**
     * Render kalitesini ayarla
     */
    function setQuality(quality) {
        settings.quality = quality;
        
        if (currentTileset) {
            currentTileset.maximumScreenSpaceError = 
                quality === 'ultra' ? 1 : 
                quality === 'high' ? 4 : 
                quality === 'medium' ? 8 : 16;
        }
        
        const scene = viewer.scene;
        scene.postProcessStages.fxaa.enabled = (quality === 'high' || quality === 'ultra');
        
        if (viewer.shadowMap.enabled) {
            viewer.shadowMap.size = quality === 'ultra' ? 4096 : 2048;
        }
    }

    /**
     * Point Cloud nokta boyutunu ayarla
     */
    function setPointSize(size) {
        settings.pointSize = size;
        
        // Tüm primitive'leri kontrol et ve point cloud olanları güncelle
        const primitives = viewer.scene.primitives;
        for (let i = 0; i < primitives.length; i++) {
            const primitive = primitives.get(i);
            
            // 3D Tileset ise ve point cloud shading desteği varsa
            if (primitive && primitive.isCesium3DTileset) {
                // Point cloud shading ayarları
                if (primitive.pointCloudShading) {
                    // Geometrik hata bazlı attenuation (uzaklığa göre boyut)
                    primitive.pointCloudShading.geometricErrorScale = size / 3;
                    primitive.pointCloudShading.maximumAttenuation = size * 4;
                    primitive.pointCloudShading.baseResolution = undefined;
                    primitive.pointCloudShading.attenuation = true;
                }
                
                // Style ile nokta boyutu ayarla (point cloud tilesetler için)
                try {
                    primitive.style = new Cesium.Cesium3DTileStyle({
                        pointSize: size.toString()
                    });
                } catch (e) {
                    // Style desteklenmiyorsa sessizce devam et
                }
            }
        }
        
        // Current tileset için de uygula
        if (currentTileset) {
            if (currentTileset.pointCloudShading) {
                currentTileset.pointCloudShading.geometricErrorScale = size / 3;
                currentTileset.pointCloudShading.maximumAttenuation = size * 4;
                currentTileset.pointCloudShading.attenuation = true;
            }
            
            try {
                currentTileset.style = new Cesium.Cesium3DTileStyle({
                    pointSize: size.toString()
                });
            } catch (e) {
                // Style desteklenmiyorsa sessizce devam et
            }
        }
        
        console.log('Cesium Point Cloud boyutu ayarlandı:', size);
    }

    /**
     * Katmanı göster/gizle
     */
    function setLayerVisibility(layerId, visible) {
        switch(layerId) {
            case 'molla-husrev-exterior':
                if (currentTileset) currentTileset.show = visible;
                break;
            case 'lod0-context':
                if (contextTileset) contextTileset.show = visible;
                break;
        }
    }

    /**
     * Ölçüm araçları
     */
    const measurements = {
        activeHandler: null,
        
        // Mesafe ölçümü
        measureDistance: function() {
            if (this.activeHandler) {
                this.activeHandler.destroy();
            }
            
            const positions = [];
            const polyline = viewer.entities.add({
                polyline: {
                    positions: new Cesium.CallbackProperty(() => positions, false),
                    width: 3,
                    material: new Cesium.PolylineGlowMaterialProperty({
                        color: Cesium.Color.GOLD,
                        glowPower: 0.2
                    }),
                    clampToGround: true
                }
            });
            
            this.activeHandler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
            
            this.activeHandler.setInputAction((click) => {
                const earthPosition = viewer.scene.pickPosition(click.position);
                if (Cesium.defined(earthPosition)) {
                    positions.push(earthPosition);
                    
                    if (positions.length === 2) {
                        const distance = Cesium.Cartesian3.distance(positions[0], positions[1]);
                        console.log('Mesafe:', distance.toFixed(2), 'm');
                        alert(`Mesafe: ${distance.toFixed(2)} m`);
                        this.activeHandler.destroy();
                        this.activeHandler = null;
                    }
                }
            }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
        },
        
        // Ölçümü temizle
        clearMeasurements: function() {
            if (this.activeHandler) {
                this.activeHandler.destroy();
                this.activeHandler = null;
            }
            // Tüm measurement entity'lerini temizle
            viewer.entities.removeAll();
        }
    };

    /**
     * FPS sayacı
     */
    function startFPSCounter() {
        let lastTime = performance.now();
        let frameCount = 0;
        
        function updateFPS() {
            frameCount++;
            const currentTime = performance.now();
            
            if (currentTime - lastTime >= 1000) {
                const fps = Math.round(frameCount * 1000 / (currentTime - lastTime));
                const fpsElement = document.getElementById('fps-counter');
                if (fpsElement) {
                    fpsElement.textContent = `${fps} FPS`;
                }
                frameCount = 0;
                lastTime = currentTime;
            }
            
            requestAnimationFrame(updateFPS);
        }
        
        updateFPS();
    }

    /**
     * Viewer'ı temizle
     */
    function destroy() {
        if (viewer) {
            viewer.destroy();
            viewer = null;
            currentTileset = null;
            contextTileset = null;
        }
    }

    // Public API
    return {
        initialize,
        initializeToken,
        loadTileset,
        loadFromIonAssetId,
        loadContextModel,
        loadDemoBuildings,
        
        // Navigation
        flyToHome,
        flyTo,
        flyToTileset,
        zoomIn,
        zoomOut,
        toggleFullscreen,
        
        // Orbit Controls
        enableOrbitAroundModel,
        lockOrbitToModel,
        unlockOrbit,
        
        // Settings
        setShadows,
        setTerrain,
        setQuality,
        setPointSize,
        setLayerVisibility,
        setBasemap,
        getBasemapList,
        
        // Measurements
        measurements,
        
        // Utils
        startFPSCounter,
        destroy,
        
        // Getters
        getViewer: () => viewer,
        getTileset: () => currentTileset,
        getSettings: () => ({ ...settings }),
        isTokenLoaded: () => tokenLoaded
    };
})();

// Global erişim için
window.CesiumViewer = CesiumViewer;


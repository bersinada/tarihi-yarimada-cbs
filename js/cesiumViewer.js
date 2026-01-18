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

    // Tarihi Yarımada merkez koordinatları (İstanbul)
    const TARIHI_YARIMADA_CENTER = {
        longitude: 28.9562,  // Sultanahmet civarı
        latitude: 40.9538,
        height: 7500         // Tüm yarımadayı görmek için yükseklik (2500 -> 3500)
    };

    // Default kamera pozisyonu - Tarihi Yarımada genel görünümü
    const DEFAULT_CAMERA = {
        destination: Cesium.Cartesian3.fromDegrees(
            TARIHI_YARIMADA_CENTER.longitude,
            TARIHI_YARIMADA_CENTER.latitude,  // Merkezde tut (offset kaldırıldı)
            TARIHI_YARIMADA_CENTER.height
        ),
        orientation: {
            heading: Cesium.Math.toRadians(0),       // Kuzeye bak
            pitch: Cesium.Math.toRadians(-50),       // Daha yukarıdan bak (-45 -> -50)
            roll: 0.0
        }
    };

    // Ayarlar
    const settings = {
        shadows: true,
        terrainEnabled: false, // Terrain kapalı - model konumu değişmesin
        globeVisible: true, // Altlık harita görünürlüğü
        quality: 'high', // Varsayılan kalite: Yüksek
        currentBasemap: 'satellite', // Varsayılan olarak uydu görüntüsü
        pointSize: 5 // Point cloud nokta boyutu
    };
    
    // Yüklenen tüm tilesetler (asset ID -> tileset)
    let loadedTilesets = {};
    
    // Model yükseklik offset'leri (metre cinsinden)
    // Pozitif = yukarı, Negatif = aşağı
    const MODEL_HEIGHT_OFFSETS = {
        '4270999': 0,  // Dış cephe
        '4271001': 0,  // İç mekan 1
        '4275532': 0,  // İç mekan 2
        '4277312': 0,  // Şadırvan
        '4318496': 0   // Sultanahmet Camii
    };

    // Altlık harita sağlayıcıları
    // Düz yüzeyli altlık harita (terrain kapalı)
    const basemapProviders = {
        // Cesium Ion Uydu Görüntüsü - Düz yüzeyli
        satellite: async () => {
            try {
                // Düz yüzeyli altlık harita
                viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
                viewer.scene.globe.depthTestAgainstTerrain = false;
                
                // Uydu görüntüsü
                return await Cesium.IonImageryProvider.fromAssetId(2);
            } catch (e) {
                console.warn('Cesium Ion yüklenemedi:', e);
                viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
                return new Cesium.ArcGisMapServerImageryProvider({
                    url: 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'
                });
            }
        },
        
        // OpenStreetMap - Sokak haritası - Düz yüzeyli
        osm: async () => {
            viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
            viewer.scene.globe.depthTestAgainstTerrain = false;
            
            return new Cesium.UrlTemplateImageryProvider({
                url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                credit: 'OpenStreetMap contributors',
                maximumLevel: 19
            });
        },
        
        // OpenTopoMap - Topografik harita - Düz yüzeyli
        openTopo: async () => {
            viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
            viewer.scene.globe.depthTestAgainstTerrain = false;
            
            return new Cesium.UrlTemplateImageryProvider({
                url: 'https://tile.opentopomap.org/{z}/{x}/{y}.png',
                credit: 'OpenTopoMap',
                maximumLevel: 17
            });
        },
        
        // Stamen Terrain - Görsel arazi haritası - Düz yüzeyli
        stamenTerrain: async () => {
            viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
            viewer.scene.globe.depthTestAgainstTerrain = false;
            
            return new Cesium.UrlTemplateImageryProvider({
                url: 'https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}.png',
                credit: 'Stamen Design',
                maximumLevel: 18
            });
        },
        
        // CartoDB Positron - Açık minimal - Düz yüzeyli
        cartoPositron: async () => {
            viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
            viewer.scene.globe.depthTestAgainstTerrain = false;
            
            return new Cesium.UrlTemplateImageryProvider({
                url: 'https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
                credit: 'CartoDB',
                maximumLevel: 19
            });
        },
        
        // CartoDB Dark Matter - Koyu tema - Düz yüzeyli
        cartoDark: async () => {
            viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
            viewer.scene.globe.depthTestAgainstTerrain = false;
            
            return new Cesium.UrlTemplateImageryProvider({
                url: 'https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
                credit: 'CartoDB',
                maximumLevel: 19
            });
        },
        
        // CartoDB Voyager - Renkli detaylı - Düz yüzeyli
        cartoVoyager: async () => {
            viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
            viewer.scene.globe.depthTestAgainstTerrain = false;
            
            return new Cesium.UrlTemplateImageryProvider({
                url: 'https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
                credit: 'CartoDB',
                maximumLevel: 19
            });
        }
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
        console.log('Cesium başlatılıyor... Container:', containerId);
        console.log('API Base URL:', apiBaseUrl);

        try {
            // Önce token'ı backend'den yükle
            console.log('Token yükleniyor...');
            await initializeToken(apiBaseUrl);
            console.log('Token başarıyla yüklendi');

            // Container var mı kontrol et
            const container = document.getElementById(containerId);
            if (!container) {
                throw new Error(`Container bulunamadı: ${containerId}`);
            }
            console.log('Container bulundu:', container);

            // Viewer oluştur
            console.log('Cesium.Viewer oluşturuluyor...');
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
            
            // Düz yüzeyli altlık harita (terrain yok)
            viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
            viewer.scene.globe.depthTestAgainstTerrain = false;
            viewer.scene.globe.show = true; // Globe'u her zaman göster
            console.log('Düz yüzeyli altlık harita aktif (terrain kapalı)');

            // Scene ayarları
            configureScene();

            // Zoom sınırlarını ayarla - Optimize edilmiş
            const controller = viewer.scene.screenSpaceCameraController;
            controller.minimumZoomDistance = 5; // 5 metre minimum (modelin içine fazla girmemesi için)
            controller.maximumZoomDistance = 50000000; // 50.000 km maksimum (dünya görünümü için)

            // Kamera hareketlerini yumuşatmak için inertia ayarları
            controller.inertiaSpin = 0.95;
            controller.inertiaTranslate = 0.95;
            controller.inertiaZoom = 0.85;

            // Collision detection - Modele çarpmayı önle
            viewer.scene.screenSpaceCameraController.enableCollisionDetection = true;

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

            // Tileset'in asset ID'sini bul
            const tileset = feature.primitive;
            let clickedAssetId = null;

            // Önce _assetId veya assetId property'sini kontrol et
            if (tileset._assetId) {
                clickedAssetId = tileset._assetId.toString();
            } else if (tileset.assetId) {
                clickedAssetId = tileset.assetId.toString();
            }

            // Eğer asset ID bulunamazsa, loadedTilesets'ten ara
            if (!clickedAssetId) {
                for (const [assetId, loadedTileset] of Object.entries(loadedTilesets)) {
                    if (loadedTileset === tileset) {
                        clickedAssetId = assetId;
                        break;
                    }
                }
            }

            console.log('Tıklanan modelin Asset ID:', clickedAssetId);

            // Main app'e bildir (window.App.selectAsset kullanarak)
            if (clickedAssetId && window.AssetsData) {
                // Asset ID ile eseri backend verilerinden bul
                const asset = window.AssetsData.assets.find(a =>
                    a.ionAssetIds.some(layer => layer.id.toString() === clickedAssetId)
                );

                if (asset && window.App && window.App.selectAsset) {
                    console.log('Eser bulundu:', asset.name);
                    window.App.selectAsset(asset.id);
                } else {
                    console.log('Bu modele ait eser bulunamadı');
                }
            }

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
     * Tileset'e yükseklik offset'i uygula (modeli zemine oturtmak için)
     * @param {Cesium.Cesium3DTileset} tileset - 3D Tileset
     * @param {number} heightOffset - Yükseklik offset (metre, negatif = aşağı)
     */
    function applyHeightOffset(tileset, heightOffset) {
        // Tileset hazır olduğunda offset uygula
        const boundingSphere = tileset.boundingSphere;
        const cartographic = Cesium.Cartographic.fromCartesian(boundingSphere.center);
        
        // Orijinal konum
        const originalPosition = Cesium.Cartesian3.fromRadians(
            cartographic.longitude,
            cartographic.latitude,
            cartographic.height
        );
        
        // Offset uygulanmış konum
        const offsetPosition = Cesium.Cartesian3.fromRadians(
            cartographic.longitude,
            cartographic.latitude,
            cartographic.height + heightOffset
        );
        
        // Translation vektörü
        const translation = Cesium.Cartesian3.subtract(
            offsetPosition,
            originalPosition,
            new Cesium.Cartesian3()
        );
        
        // Model matrix'i güncelle
        tileset.modelMatrix = Cesium.Matrix4.fromTranslation(translation);
        
        console.log(`Model height offset uygulandı: ${heightOffset}m`);
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
            
            // Görünürlük ayarı (varsayılan: true, options'dan override edilebilir)
            tileset.show = options.show !== undefined ? options.show : true;
            
            // Modeli zemine oturtmak için height offset uygula
            const heightOffset = MODEL_HEIGHT_OFFSETS[assetId.toString()] || 0;
            if (heightOffset !== 0) {
                applyHeightOffset(tileset, heightOffset);
            }
            
            // Tileset'i kaydet
            loadedTilesets[assetId.toString()] = tileset;
            
            // Dış cephe (4270999) yüklenirse currentTileset olarak ayarla
            // Bu, orbit modunda doğru merkezi seçmek için önemli
            if (assetId.toString() === '4270999') {
                currentTileset = tileset;
                console.log('Dış cephe katmanı currentTileset olarak ayarlandı');
            } else if (!currentTileset) {
                // Eğer currentTileset yoksa, ilk yüklenen tileset'i ayarla
                currentTileset = tileset;
            }
            
            // Tileset yüklendiğinde kamerası yakınlaştır
            if (options.zoomTo !== false) {
                await viewer.zoomTo(tileset);
            }

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
     * Öncelik: Dış cephe (4270999) > Diğer katmanlar
     */
    function enableOrbitAroundModel() {
        // Öncelik: Dış cephe katmanını (4270999) bul
        const PRIMARY_ASSET_ID = '4270999'; // Dış cephe - Ana camii
        
        let tileset = null;
        
        // 1. Önce dış cephe katmanını (4270999) yüklü tilesetlerden ara
        if (loadedTilesets[PRIMARY_ASSET_ID]) {
            tileset = loadedTilesets[PRIMARY_ASSET_ID];
            console.log('enableOrbitAroundModel: Dış cephe katmanı (4270999) bulundu');
        }
        
        // 2. Scene'deki primitives'lerden dış cephe katmanını ara
        if (!tileset) {
            const primitives = viewer.scene.primitives;
            for (let i = 0; i < primitives.length; i++) {
                const primitive = primitives.get(i);
                if (primitive && primitive.isCesium3DTileset) {
                    const primitiveAssetId = primitive._assetId || primitive.assetId;
                    if (primitiveAssetId && primitiveAssetId.toString() === PRIMARY_ASSET_ID) {
                        tileset = primitive;
                        console.log('enableOrbitAroundModel: Scene\'de dış cephe katmanı (4270999) bulundu');
                        break;
                    }
                }
            }
        }
        
        // 3. Dış cephe bulunamazsa, currentTileset'i dene
        if (!tileset && currentTileset) {
            tileset = currentTileset;
            console.log('enableOrbitAroundModel: currentTileset kullanılıyor');
        }
        
        // 4. Hala yoksa, loadedTilesets'ten şadırvan hariç ilkini al
        if (!tileset) {
            const tilesetKeys = Object.keys(loadedTilesets);
            if (tilesetKeys.length > 0) {
                const nonSadirvanKeys = tilesetKeys.filter(key => key !== '4277312');
                if (nonSadirvanKeys.length > 0) {
                    tileset = loadedTilesets[nonSadirvanKeys[0]];
                    console.log('enableOrbitAroundModel: loadedTilesets\'ten tileset kullanılıyor:', nonSadirvanKeys[0]);
                }
            }
        }
        
        if (!tileset) {
            console.warn('Tileset yüklenmemiş, orbit modu aktifleştirilemiyor');
            return;
        }

        // Tileset'in bounding sphere'ini al
        const boundingSphere = tileset.boundingSphere;
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

        console.log('Orbit modu aktifleştirildi - Dış cephe merkezine odaklandı');
    }

    /**
     * Model etrafında orbit - mevcut pozisyonda kilitle
     * Bu mod aktifken kamera mevcut pozisyon etrafında döner
     * Artık belirli bir modele gitmez, o anki kamera pozisyonunu merkez alır
     */
    function lockOrbitToModel() {
        // Mevcut kamera pozisyonunu al
        const cameraPosition = viewer.camera.position;
        
        // Kameranın baktığı yönü al (pick ray ile)
        const direction = viewer.camera.direction;
        
        // Kameranın baktığı noktayı hesapla (yaklaşık 100m ileride)
        const lookAtPoint = Cesium.Cartesian3.add(
            cameraPosition,
            Cesium.Cartesian3.multiplyByScalar(direction, 100, new Cesium.Cartesian3()),
            new Cesium.Cartesian3()
        );
        
        // Transform matrisini oluştur (mevcut bakış noktası etrafında)
        const transform = Cesium.Transforms.eastNorthUpToFixedFrame(lookAtPoint);
        
        // Mevcut kamera mesafesini hesapla
        const currentDistance = Cesium.Cartesian3.distance(cameraPosition, lookAtPoint);
        
        // Kamerayı bu transform'a kilitle (mevcut pozisyonu koruyarak)
        viewer.camera.lookAtTransform(
            transform,
            new Cesium.HeadingPitchRange(
                viewer.camera.heading,
                viewer.camera.pitch,
                currentDistance
            )
        );

        console.log('Kamera mevcut pozisyonda orbit moduna kilitlendi');
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
        settings.terrainEnabled = enabled;

        // Globe'u her zaman göster (sadece terrain ayarı değiştir)
        viewer.scene.globe.show = true;

        // Terrain provider değiştir
        if (enabled) {
            // Terrain enabled - daha detaylı arazi
            viewer.terrainProvider = Cesium.createWorldTerrain();
            viewer.scene.globe.depthTestAgainstTerrain = true;
        } else {
            // Terrain disabled - düz yüzey
            viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
            viewer.scene.globe.depthTestAgainstTerrain = false;
        }

        // Modelin her zaman görünür kalmasını sağla
        if (currentTileset) {
            currentTileset.show = true;
        }

        console.log('Terrain:', enabled ? 'aktif' : 'kapalı', '(Globe her zaman görünür)');
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
            { id: 'satellite', name: 'Uydu Görüntüsü', category: 'satellite', description: 'Cesium Ion Uydu Görüntüsü' },
            
            // Sokak Haritası
            { id: 'osm', name: 'OpenStreetMap', category: 'street', description: 'Sokak haritası' },
            
            // CartoDB
            { id: 'cartoPositron', name: 'CartoDB Açık', category: 'minimal', description: 'Açık minimal tema' },
            { id: 'cartoDark', name: 'CartoDB Koyu', category: 'minimal', description: 'Koyu minimal tema' }
        ];
    }

    /**
     * Render kalitesini ayarla
     */
    function setQuality(quality) {
        if (!viewer) {
            console.warn('Viewer başlatılmamış');
            return;
        }
        
        settings.quality = quality;
        
        // Kalite parametreleri
        const screenSpaceError = 
            quality === 'ultra' ? 1 : 
            quality === 'high' ? 4 : 
            quality === 'medium' ? 8 : 16;
        
        // Tüm yüklenen tilesetlere uygula
        Object.values(loadedTilesets).forEach(tileset => {
            if (tileset) {
                tileset.maximumScreenSpaceError = screenSpaceError;
            }
        });
        
        // Current tileset için de uygula
        if (currentTileset) {
            currentTileset.maximumScreenSpaceError = screenSpaceError;
        }
        
        // Scene'deki tüm primitives'leri kontrol et ve tileset olanları güncelle
        const primitives = viewer.scene.primitives;
        for (let i = 0; i < primitives.length; i++) {
            const primitive = primitives.get(i);
            if (primitive && primitive.isCesium3DTileset) {
                primitive.maximumScreenSpaceError = screenSpaceError;
            }
        }
        
        // Scene ayarları
        const scene = viewer.scene;
        scene.postProcessStages.fxaa.enabled = (quality === 'high' || quality === 'ultra');
        
        // Gölge kalitesi
        if (viewer.shadowMap.enabled) {
            viewer.shadowMap.size = quality === 'ultra' ? 4096 : 2048;
        }
        
        // Resolution scale
        if (quality === 'ultra') {
            viewer.resolutionScale = 1.5;
        } else if (quality === 'high') {
            viewer.resolutionScale = 1.25;
        } else if (quality === 'medium') {
            viewer.resolutionScale = 1.0;
        } else {
            viewer.resolutionScale = 0.75;
        }
        
        console.log('Render kalitesi ayarlandı:', quality, '(SSE:', screenSpaceError, ')');
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
     * @param {string} layerIdOrAssetId - Katman ID veya Asset ID
     * @param {boolean} visible - Görünürlük durumu
     */
    function setLayerVisibility(layerIdOrAssetId, visible) {
        if (!viewer) {
            console.warn('Viewer başlatılmamış');
            return;
        }
        
        let tilesetFound = false;
        
        // Önce asset ID olarak dene
        if (loadedTilesets[layerIdOrAssetId]) {
            loadedTilesets[layerIdOrAssetId].show = visible;
            console.log(`Tileset ${layerIdOrAssetId} görünürlük: ${visible} (loadedTilesets)`);
            tilesetFound = true;
        }
        
        // Legacy layer ID'ler için
        switch(layerIdOrAssetId) {
            case 'exterior':
            case 'molla-husrev-exterior':
            case '4270999':
                if (loadedTilesets['4270999']) {
                    loadedTilesets['4270999'].show = visible;
                    tilesetFound = true;
                } else if (currentTileset) {
                    currentTileset.show = visible;
                    tilesetFound = true;
                }
                break;
            case 'interior-1':
            case '4271001':
                if (loadedTilesets['4271001']) {
                    loadedTilesets['4271001'].show = visible;
                    tilesetFound = true;
                }
                break;
            case 'interior-2':
            case '4275532':
                if (loadedTilesets['4275532']) {
                    loadedTilesets['4275532'].show = visible;
                    tilesetFound = true;
                }
                break;
            case 'sadirvan':
            case '4277312':
                if (loadedTilesets['4277312']) {
                    loadedTilesets['4277312'].show = visible;
                    tilesetFound = true;
                }
                break;
            case 'sultanahmet':
            case '4318496':
                if (loadedTilesets['4318496']) {
                    loadedTilesets['4318496'].show = visible;
                    tilesetFound = true;
                }
                break;
            case 'lod0-context':
                if (contextTileset) {
                    contextTileset.show = visible;
                    tilesetFound = true;
                }
                break;
        }
        
        // Scene'deki primitives'lerden de kontrol et
        const primitives = viewer.scene.primitives;
        for (let i = 0; i < primitives.length; i++) {
            const primitive = primitives.get(i);
            if (primitive && primitive.isCesium3DTileset) {
                // Asset ID'yi kontrol et (eğer varsa)
                const primitiveAssetId = primitive._assetId || primitive.assetId;
                if (primitiveAssetId && primitiveAssetId.toString() === layerIdOrAssetId) {
                    primitive.show = visible;
                    console.log(`Primitive tileset görünürlük ayarlandı: ${layerIdOrAssetId} = ${visible}`);
                    tilesetFound = true;
                }
            }
        }
        
        if (!tilesetFound) {
            console.warn('Katman bulunamadı:', layerIdOrAssetId);
        }
    }
    
    /**
     * Belirli bir tileset'i getir
     */
    function getTilesetByAssetId(assetId) {
        return loadedTilesets[assetId.toString()];
    }
    
    /**
     * Tüm yüklenen tilesetleri getir
     */
    function getAllTilesets() {
        return { ...loadedTilesets };
    }

    /**
     * Model yükseklik offset'ini ayarla
     * @param {string} assetId - Asset ID
     * @param {number} heightOffset - Yükseklik offset (metre, negatif = aşağı)
     */
    function setModelHeightOffset(assetId, heightOffset) {
        const tileset = loadedTilesets[assetId.toString()];
        if (tileset) {
            applyHeightOffset(tileset, heightOffset);
            // MODEL_HEIGHT_OFFSETS const olduğu için güncellenemez, sadece kullanılır
            console.log(`Model ${assetId} height offset: ${heightOffset}m`);
        } else {
            console.warn('Tileset bulunamadı:', assetId);
        }
    }

    /**
     * Tüm modellerin yükseklik offset'ini ayarla
     * @param {number} heightOffset - Yükseklik offset (metre)
     */
    function setAllModelsHeightOffset(heightOffset) {
        Object.keys(loadedTilesets).forEach(assetId => {
            setModelHeightOffset(assetId, heightOffset);
        });
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
        
        // Model Position
        setModelHeightOffset,
        setAllModelsHeightOffset,
        applyHeightOffset,
        
        // Measurements
        measurements,
        
        // Utils
        startFPSCounter,
        destroy,
        
        // Getters
        getViewer: () => viewer,
        getTileset: () => currentTileset,
        getTilesetByAssetId,
        getAllTilesets,
        getSettings: () => ({ ...settings }),
        isTokenLoaded: () => tokenLoaded
    };
})();

// Global erişim için
window.CesiumViewer = CesiumViewer;


/**
 * Tarihi Yarımada CBS - Potree Viewer Module
 * Point Cloud ve iç mekan görselleştirmesi
 */

const PotreeViewer = (function() {
    // Viewer instance
    let viewer = null;
    let currentPointCloud = null;

    // Molla Hüsrev Camii koordinatları (iç mekan için)
    const MOLLA_HUSREV_INTERIOR = {
        x: 0,
        y: 0,
        z: 5
    };

    // Potree yüklü mü kontrol et
    const isPotreeLoaded = typeof Potree !== 'undefined';
    
    // Ayarlar
    const settings = {
        pointSize: 3,
        pointSizeType: isPotreeLoaded ? (Potree.PointSizeType?.ADAPTIVE || 1) : 1,
        pointShape: isPotreeLoaded ? (Potree.PointShape?.CIRCLE || 1) : 1,
        quality: 'medium',
        edlEnabled: true,
        edlStrength: 0.4,
        edlRadius: 1.4,
        background: 'gradient'
    };

    /**
     * Potree Viewer'ı başlat
     */
    function initialize(containerId) {
        if (!isPotreeLoaded) {
            console.warn('Potree kütüphanesi yüklenmedi');
            return null;
        }
        
        if (viewer) {
            console.warn('Potree Viewer zaten başlatılmış');
            return viewer;
        }

        try {
            const container = document.getElementById(containerId);
            if (!container) {
                throw new Error(`Container bulunamadı: ${containerId}`);
            }

            // Potree Viewer oluştur
            viewer = new Potree.Viewer(container);

            // Temel ayarlar
            configureViewer();

            // Background ayarla
            setBackground(settings.background);

            // Kontrolleri ayarla
            setupControls();

            console.log('Potree Viewer başarıyla başlatıldı');
            return viewer;

        } catch (error) {
            console.error('Potree Viewer başlatılamadı:', error);
            throw error;
        }
    }

    /**
     * Viewer ayarlarını yapılandır
     */
    function configureViewer() {
        // EDL (Eye-Dome Lighting) - Derinlik algısını artırır
        viewer.setEDLEnabled(settings.edlEnabled);
        viewer.setEDLStrength(settings.edlStrength);
        viewer.setEDLRadius(settings.edlRadius);

        // Point ayarları
        viewer.setPointBudget(2_000_000); // 2 milyon point
        
        // FOV
        viewer.setFOV(60);

        // Clipping
        viewer.setClipTask(Potree.ClipTask.HIGHLIGHT);
        viewer.setClipMethod(Potree.ClipMethod.INSIDE_ANY);

        // Navigation
        viewer.setNavigationMode(Potree.NavigationCube);
        
        // Minimum node size
        viewer.setMinNodeSize(30);
    }

    /**
     * Kontrolleri ayarla
     */
    function setupControls() {
        // Orbit controls için ayarlar
        const controls = viewer.getControls();
        if (controls) {
            // Orbit hızı
            if (controls.orbitSpeed !== undefined) {
                controls.orbitSpeed = 1.5;
            }
        }

        // Input controls
        viewer.setMoveSpeed(10);
    }

    /**
     * Point Cloud yükle
     */
    async function loadPointCloud(url, name = 'PointCloud') {
        if (!viewer) {
            throw new Error('Viewer başlatılmamış');
        }

        try {
            return new Promise((resolve, reject) => {
                Potree.loadPointCloud(url, name, (e) => {
                    if (e.type === 'loading_failed') {
                        reject(new Error('Point Cloud yüklenemedi'));
                        return;
                    }

                    const pointCloud = e.pointcloud;
                    viewer.scene.addPointCloud(pointCloud);

                    // Material ayarları
                    const material = pointCloud.material;
                    material.size = settings.pointSize;
                    material.pointSizeType = settings.pointSizeType;
                    material.shape = settings.pointShape;
                    
                    // Renk modunu ayarla (RGB veya Height)
                    material.activeAttributeName = 'rgba';

                    // Point Cloud'a uç
                    viewer.fitToScreen();

                    currentPointCloud = pointCloud;
                    console.log('Point Cloud yüklendi:', url);
                    
                    resolve(pointCloud);
                });
            });

        } catch (error) {
            console.error('Point Cloud yüklenemedi:', error);
            throw error;
        }
    }

    /**
     * Demo point cloud yükle (Potree örnek verisi)
     */
    async function loadDemoPointCloud() {
        // Potree'nin örnek point cloud'larından birini yükle
        const demoUrl = 'https://5d.nuernberg.de/2021/kirche/pointclouds/kirche/metadata.json';
        
        try {
            return await loadPointCloud(demoUrl, 'Demo Church');
        } catch (error) {
            console.warn('Demo point cloud yüklenemedi, boş sahne gösterilecek');
            return null;
        }
    }

    /**
     * Background ayarla
     */
    function setBackground(type) {
        settings.background = type;
        
        switch(type) {
            case 'skybox':
                viewer.setBackground('skybox');
                break;
            case 'gradient':
                viewer.setBackground('gradient');
                break;
            case 'black':
                viewer.setBackground('black');
                break;
            case 'white':
                viewer.setBackground('white');
                break;
            default:
                viewer.setBackground('gradient');
        }
    }

    /**
     * Point boyutunu ayarla
     */
    function setPointSize(size) {
        settings.pointSize = size;
        
        // Viewer varsa tüm point cloud'ları güncelle
        if (viewer && viewer.scene && viewer.scene.pointclouds) {
            viewer.scene.pointclouds.forEach(pc => {
                if (pc && pc.material) {
                    pc.material.size = size;
                }
            });
        }
        
        // Mevcut point cloud'u da güncelle (eski yöntem - yedek)
        if (currentPointCloud && currentPointCloud.material) {
            currentPointCloud.material.size = size;
        }
        
        console.log('Point Cloud boyutu ayarlandı:', size);
    }

    /**
     * Render kalitesini ayarla
     */
    function setQuality(quality) {
        settings.quality = quality;
        
        const budgets = {
            low: 500_000,
            medium: 2_000_000,
            high: 5_000_000,
            ultra: 10_000_000
        };
        
        viewer.setPointBudget(budgets[quality] || budgets.medium);
        
        // Min node size
        const minNodeSizes = {
            low: 100,
            medium: 30,
            high: 10,
            ultra: 5
        };
        
        viewer.setMinNodeSize(minNodeSizes[quality] || 30);
    }

    /**
     * EDL ayarla
     */
    function setEDL(enabled, strength = 0.4, radius = 1.4) {
        settings.edlEnabled = enabled;
        settings.edlStrength = strength;
        settings.edlRadius = radius;
        
        viewer.setEDLEnabled(enabled);
        if (enabled) {
            viewer.setEDLStrength(strength);
            viewer.setEDLRadius(radius);
        }
    }

    /**
     * Kamerası sıfırla
     */
    function resetCamera() {
        viewer.fitToScreen();
    }

    /**
     * Yakınlaştır
     */
    function zoomIn() {
        const camera = viewer.scene.getActiveCamera();
        if (camera) {
            camera.position.multiplyScalar(0.8);
        }
    }

    /**
     * Uzaklaştır
     */
    function zoomOut() {
        const camera = viewer.scene.getActiveCamera();
        if (camera) {
            camera.position.multiplyScalar(1.2);
        }
    }

    /**
     * Tam ekran modu
     */
    function toggleFullscreen() {
        const container = viewer.renderer.domElement.parentElement;
        if (!document.fullscreenElement) {
            container.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    }

    /**
     * Katman görünürlüğü
     */
    function setLayerVisibility(layerId, visible) {
        if (layerId === 'molla-husrev-interior' && currentPointCloud) {
            currentPointCloud.visible = visible;
        }
    }

    /**
     * Renk modunu değiştir
     */
    function setColorMode(mode) {
        if (currentPointCloud && currentPointCloud.material) {
            switch(mode) {
                case 'rgb':
                    currentPointCloud.material.activeAttributeName = 'rgba';
                    break;
                case 'height':
                    currentPointCloud.material.activeAttributeName = 'elevation';
                    break;
                case 'intensity':
                    currentPointCloud.material.activeAttributeName = 'intensity';
                    break;
                case 'classification':
                    currentPointCloud.material.activeAttributeName = 'classification';
                    break;
            }
        }
    }

    /**
     * Ölçüm araçları
     */
    const measurements = {
        activeTool: null,
        
        // Mesafe ölçümü
        measureDistance: function() {
            this.clearActiveTool();
            const measure = viewer.measuringTool.startInsertion({
                showDistances: true,
                showAngles: false,
                showCoordinates: false,
                showArea: false,
                closed: false,
                name: 'Mesafe'
            });
            this.activeTool = measure;
        },
        
        // Alan ölçümü
        measureArea: function() {
            this.clearActiveTool();
            const measure = viewer.measuringTool.startInsertion({
                showDistances: true,
                showAngles: true,
                showCoordinates: false,
                showArea: true,
                closed: true,
                name: 'Alan'
            });
            this.activeTool = measure;
        },
        
        // Yükseklik ölçümü
        measureHeight: function() {
            this.clearActiveTool();
            const measure = viewer.measuringTool.startInsertion({
                showDistances: false,
                showHeight: true,
                showCoordinates: false,
                maxMarkers: 2,
                name: 'Yükseklik'
            });
            this.activeTool = measure;
        },
        
        // Anotasyon ekle
        addAnnotation: function(title, description) {
            const annotation = new Potree.Annotation({
                title: title || 'Yeni Not',
                description: description || '',
                position: viewer.scene.view.position.clone()
            });
            viewer.scene.annotations.add(annotation);
            return annotation;
        },
        
        // Aktif aracı temizle
        clearActiveTool: function() {
            if (this.activeTool) {
                viewer.scene.removeMeasurement(this.activeTool);
                this.activeTool = null;
            }
        },
        
        // Tüm ölçümleri temizle
        clearAllMeasurements: function() {
            this.clearActiveTool();
            viewer.scene.removeAllMeasurements();
        }
    };

    /**
     * Clipping box ekle
     */
    function addClippingVolume() {
        const volume = viewer.volumeTool.startInsertion({
            clip: true
        });
        return volume;
    }

    /**
     * Screenshot al
     */
    function takeScreenshot() {
        const screenshot = viewer.renderer.domElement.toDataURL('image/png');
        
        // Download link oluştur
        const link = document.createElement('a');
        link.href = screenshot;
        link.download = `tarihi-yarimada-${Date.now()}.png`;
        link.click();
        
        return screenshot;
    }

    /**
     * Point Cloud istatistikleri
     */
    function getStatistics() {
        if (!currentPointCloud) {
            return null;
        }

        return {
            name: currentPointCloud.name,
            pointCount: currentPointCloud.numPoints,
            boundingBox: currentPointCloud.boundingBox,
            spacing: currentPointCloud.spacing,
            scale: currentPointCloud.scale
        };
    }

    /**
     * Viewer'ı temizle
     */
    function destroy() {
        if (viewer) {
            // Point cloud'ları temizle
            viewer.scene.pointclouds.forEach(pc => {
                viewer.scene.removePointCloud(pc);
            });
            
            currentPointCloud = null;
            viewer = null;
        }
    }

    // Public API
    return {
        initialize,
        loadPointCloud,
        loadDemoPointCloud,
        
        // Navigation
        resetCamera,
        zoomIn,
        zoomOut,
        toggleFullscreen,
        
        // Settings
        setBackground,
        setPointSize,
        setQuality,
        setEDL,
        setColorMode,
        setLayerVisibility,
        
        // Measurements
        measurements,
        
        // Tools
        addClippingVolume,
        takeScreenshot,
        
        // Utils
        getStatistics,
        destroy,
        
        // Getters
        getViewer: () => viewer,
        getPointCloud: () => currentPointCloud,
        getSettings: () => ({ ...settings })
    };
})();

// Global erişim için
window.PotreeViewer = PotreeViewer;


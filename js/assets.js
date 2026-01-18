/**
 * Tarihi Yarımada CBS - Assets (Eserler) Verisi
 * Backend API'den dinamik olarak yüklenir
 */

const AssetsData = {
    assets: [],
    loaded: false,

    /**
     * Backend'den tüm eserleri yükle
     */
    async loadAssets() {
        if (this.loaded) {
            console.log('Eserler zaten yüklendi');
            return this.assets;
        }

        try {
            const apiBaseUrl = this.getApiBaseUrl();
            const response = await fetch(`${apiBaseUrl}/api/v1/assets`);

            if (!response.ok) {
                throw new Error(`Assets yüklenemedi: ${response.status}`);
            }

            const backendAssets = await response.json();

            // Backend verisini frontend formatına çevir
            this.assets = backendAssets.map(asset => this.transformAsset(asset));
            this.loaded = true;

            console.log(`${this.assets.length} eser başarıyla yüklendi`);
            return this.assets;

        } catch (error) {
            console.error('Eserler yüklenirken hata:', error);
            throw error;
        }
    },

    /**
     * Backend asset verisini frontend formatına çevir
     */
    transformAsset(backendAsset) {
        // Dönem mapping
        const periodMap = {
            'bizans': 'Bizans',
            'osmanli_erken': 'Osmanlı',
            'osmanli_klasik': 'Osmanlı',
            'osmanli_gec': 'Osmanlı',
            'cumhuriyet': 'Cumhuriyet'
        };

        return {
            id: backendAsset.identifier,
            name: backendAsset.name_tr,
            period: periodMap[backendAsset.historical_period] || 'Diğer',
            year: backendAsset.construction_year,
            founder: this.getFounder(backendAsset),
            location: backendAsset.neighborhood || 'İstanbul',
            description: backendAsset.description_tr || '',
            ionAssetIds: backendAsset.cesium_ion_asset_id ? [
                {
                    id: backendAsset.cesium_ion_asset_id,
                    name: backendAsset.name_tr,
                    type: '3D Tiles',
                    visible: true
                }
            ] : [],
            position: {
                lon: backendAsset.longitude || 28.9750,
                lat: backendAsset.latitude || 41.0100,
                height: 500
            },
            metadata: {
                heritage: backendAsset.protection_status || '',
                condition: 'Restore Edilmiş',
                area: ''
            },
            // Backend verisini de sakla
            _backend: backendAsset
        };
    },

    /**
     * Kurucuyu belirle (gelecekte actors API'den çekilecek)
     */
    getFounder(asset) {
        // Şimdilik basit bir mapping
        if (asset.historical_period === 'bizans') {
            return 'I. Justinianus';
        }
        return 'Osmanlı';
    },

    /**
     * API Base URL'i otomatik tespit et
     */
    getApiBaseUrl() {
        const hostname = window.location.hostname;

        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://localhost:8000';
        }

        return window.location.origin;
    },

    /**
     * Eseri ID ile getir
     */
    getAsset(assetId) {
        return this.assets.find(a => a.id === assetId);
    },

    /**
     * Periyoda göre eserleri filtrele
     */
    getAssetsByPeriod(period) {
        return this.assets.filter(a => a.period === period);
    },

    /**
     * Tüm periyodları getir
     */
    getPeriods() {
        return [...new Set(this.assets.map(a => a.period))];
    },

    /**
     * Eserin Ion Asset ID'lerini getir
     */
    getIonAssetIds(assetId) {
        const asset = this.getAsset(assetId);
        return asset ? asset.ionAssetIds : [];
    }
};

// Global erişim
window.AssetsData = AssetsData;

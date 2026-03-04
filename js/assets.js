/**
 * Tarihi Yarımada CBS - Assets (Eserler) Verisi
 * Backend API'den dinamik olarak yüklenir
 */

const AssetsData = {
    assets: [],
    loaded: false,

    // Yapı tipi kategorileri
    buildingTypes: {
        'cami': { name: 'Camiler', icon: '', order: 1 },
        'anit': { name: 'Anıtlar ve Sütunlar', icon: '', order: 2 },
        'kilise': { name: 'Kiliseler ve Müzeler', icon: '', order: 3 },
        'turbe': { name: 'Türbeler', icon: '', order: 4 },
        'cesme': { name: 'Çeşmeler', icon: '', order: 5 },
        'saray': { name: 'Saraylar', icon: '', order: 6 },
        'diger': { name: 'Diğer Yapılar', icon: '', order: 7 }
    },

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
            buildingType: this.determineBuildingType(backendAsset),
            year: backendAsset.construction_period || this.formatYear(backendAsset.construction_year),
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
     * Yapı tipini belirle (backend'den gelen asset_type veya isimden çıkar)
     */
    determineBuildingType(asset) {
        // Backend'den gelen asset_type varsa kullan
        if (asset.asset_type) {
            const typeMap = {
                'cami': 'cami',
                'mosque': 'cami',
                'kilise': 'kilise',
                'church': 'kilise',
                'müze': 'kilise',
                'museum': 'kilise',
                'saray': 'saray',
                'palace': 'saray',
                'türbe': 'turbe',
                'tomb': 'turbe',
                'çeşme': 'cesme',
                'fountain': 'cesme',
                'anıt': 'anit',
                'monument': 'anit',
                'sütun': 'anit',
                'column': 'anit',
                'obelisk': 'anit'
            };
            const normalizedType = asset.asset_type.toLowerCase();
            if (typeMap[normalizedType]) {
                return typeMap[normalizedType];
            }
        }

        // İsimden tahmin et
        const name = (asset.name_tr || '').toLowerCase();
        if (name.includes('cami') || name.includes('mescid')) return 'cami';
        if (name.includes('kilise') || name.includes('irini') || name.includes('ayasofya')) return 'kilise';
        if (name.includes('saray')) return 'saray';
        if (name.includes('türbe')) return 'turbe';
        if (name.includes('çeşme')) return 'cesme';
        if (name.includes('dikilitaş') || name.includes('sütun') || name.includes('anıt')) return 'anit';

        return 'diger';
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
     * Yılı formatla (M.Ö. / M.S.)
     */
    formatYear(year) {
        if (!year) return '-';
        if (year < 0) {
            return `M.Ö. ${Math.abs(year)}`;
        }
        return year.toString();
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
     * Yapı tipine göre eserleri filtrele
     */
    getAssetsByBuildingType(buildingType) {
        return this.assets.filter(a => a.buildingType === buildingType);
    },

    /**
     * Tüm periyodları getir
     */
    getPeriods() {
        return [...new Set(this.assets.map(a => a.period))];
    },

    /**
     * Tüm yapı tiplerini getir (sıralı)
     */
    getBuildingTypes() {
        const usedTypes = [...new Set(this.assets.map(a => a.buildingType))];
        return usedTypes
            .filter(type => this.buildingTypes[type])
            .sort((a, b) => this.buildingTypes[a].order - this.buildingTypes[b].order);
    },

    /**
     * Yapı tipi bilgisini getir
     */
    getBuildingTypeInfo(typeKey) {
        return this.buildingTypes[typeKey] || this.buildingTypes['diger'];
    },

    /**
     * Eserin Ion Asset ID'lerini getir
     */
    getIonAssetIds(assetId) {
        const asset = this.getAsset(assetId);
        return asset ? asset.ionAssetIds : [];
    },

    /**
     * Eserin fotoğraflarını backend'den yükle
     */
    async loadAssetMedia(assetId) {
        try {
            const asset = this.getAsset(assetId);
            if (!asset || !asset._backend) {
                console.warn('Asset bulunamadı:', assetId);
                return [];
            }

            const backendId = asset._backend.id;
            const apiBaseUrl = this.getApiBaseUrl();
            const response = await fetch(`${apiBaseUrl}/api/v1/assets/${backendId}/media`);

            if (!response.ok) {
                console.warn(`Media yüklenemedi: ${response.status}`);
                return [];
            }

            const media = await response.json();
            console.log(`${assetId} için ${media.length} fotoğraf yüklendi`);
            return media;

        } catch (error) {
            console.error('Media yüklenirken hata:', error);
            return [];
        }
    }
};

// Global erişim
window.AssetsData = AssetsData;

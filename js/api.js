/**
 * Tarihi Yarımada CBS - API Module
 * FastAPI Backend ile iletişim için
 */

const API = (function() {
    // API Base URL'i otomatik tespit et
    // Production'da aynı origin kullanılır, development'ta localhost:8000
    function getBaseUrl() {
        // Eğer sayfa localhost'tan yükleniyorsa development modundayız
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            // Development: Eğer port 8000 değilse (örn: Live Server 5500 kullanıyorsa)
            if (window.location.port !== '8000') {
                return 'http://localhost:8000/api/v1';
            }
        }
        // Production veya backend'den serve ediliyorsa: aynı origin
        return `${window.location.origin}/api/v1`;
    }

    // API Konfigürasyonu
    const config = {
        baseUrl: getBaseUrl(),
        timeout: 30000,
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    };

    // API durumu
    let isConnected = false;
    let connectionListeners = [];

    /**
     * API bağlantı durumu değişikliklerini dinle
     */
    function onConnectionChange(callback) {
        connectionListeners.push(callback);
    }

    /**
     * Bağlantı durumunu güncelle
     */
    function setConnectionStatus(status) {
        isConnected = status;
        connectionListeners.forEach(cb => cb(status));
    }

    /**
     * Temel HTTP isteği
     */
    async function request(endpoint, options = {}) {
        const url = `${config.baseUrl}${endpoint}`;
        
        const fetchOptions = {
            ...options,
            headers: {
                ...config.headers,
                ...options.headers
            }
        };

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), config.timeout);
            
            const response = await fetch(url, {
                ...fetchOptions,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status} ${response.statusText}`);
            }

            setConnectionStatus(true);
            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                console.error('API isteği zaman aşımına uğradı');
            } else {
                console.error('API Hatası:', error.message);
            }
            setConnectionStatus(false);
            throw error;
        }
    }

    /**
     * GET isteği
     */
    async function get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return request(url, { method: 'GET' });
    }

    /**
     * POST isteği
     */
    async function post(endpoint, data = {}) {
        return request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT isteği
     */
    async function put(endpoint, data = {}) {
        return request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE isteği
     */
    async function del(endpoint) {
        return request(endpoint, { method: 'DELETE' });
    }

    // ============================================
    // API Endpoints
    // ============================================

    /**
     * Sağlık kontrolü
     */
    async function healthCheck() {
        try {
            const response = await get('/health');
            setConnectionStatus(true);
            return response;
        } catch (error) {
            setConnectionStatus(false);
            return null;
        }
    }

    /**
     * Yapı listesini getir
     */
    async function getBuildings(params = {}) {
        return get('/buildings', params);
    }

    /**
     * Tek bir yapıyı getir
     */
    async function getBuilding(id) {
        return get(`/buildings/${id}`);
    }

    /**
     * Yapı metadatasını getir
     */
    async function getBuildingMetadata(id) {
        return get(`/buildings/${id}/metadata`);
    }

    /**
     * 3D Tiles tileset URL'ini getir
     */
    async function getTilesetUrl(buildingId) {
        return get(`/buildings/${buildingId}/tileset`);
    }

    /**
     * Point Cloud URL'ini getir
     */
    async function getPointCloudUrl(buildingId) {
        return get(`/buildings/${buildingId}/pointcloud`);
    }

    /**
     * Katman listesini getir
     */
    async function getLayers() {
        return get('/layers');
    }

    /**
     * Katman bilgisini getir
     */
    async function getLayer(id) {
        return get(`/layers/${id}`);
    }

    /**
     * Mekansal sorgu yap
     */
    async function spatialQuery(params) {
        return post('/query/spatial', params);
    }

    /**
     * Öznitelik sorgusu yap
     */
    async function attributeQuery(params) {
        return post('/query/attribute', params);
    }

    /**
     * Ölçüm sonucunu kaydet
     */
    async function saveMeasurement(data) {
        return post('/measurements', data);
    }

    /**
     * Ölçümleri getir
     */
    async function getMeasurements(buildingId) {
        return get(`/buildings/${buildingId}/measurements`);
    }

    /**
     * Not (Açıklama) ekle
     * @param {object} data - { yapi_id, baslik, aciklama, x, y, z, olusturan }
     */
    async function addNote(data) {
        return post('/aciklamalar', data);
    }

    /**
     * Yapıya ait notları getir
     */
    async function getNotes(yapiId) {
        return get(`/yapilar/${yapiId}/aciklamalar`);
    }

    /**
     * Tüm yapıları getir (Türkçe endpoint)
     */
    async function getYapilar(params = {}) {
        return get('/yapilar', params);
    }

    /**
     * Tek yapıyı getir
     */
    async function getYapi(yapiId) {
        return get(`/yapilar/${yapiId}`);
    }

    /**
     * Coğrafi arama
     */
    async function geocode(query) {
        return get('/geocode', { q: query });
    }

    // Public API
    return {
        // Config
        config,
        
        // Connection
        isConnected: () => isConnected,
        onConnectionChange,
        healthCheck,
        
        // HTTP methods
        get,
        post,
        put,
        delete: del,
        
        // Buildings (English)
        getBuildings,
        getBuilding,
        getBuildingMetadata,
        getTilesetUrl,
        getPointCloudUrl,
        
        // Yapılar (Turkish)
        getYapilar,
        getYapi,
        
        // Layers
        getLayers,
        getLayer,
        
        // Queries
        spatialQuery,
        attributeQuery,
        
        // Measurements
        saveMeasurement,
        getMeasurements,
        
        // Notes (Açıklamalar)
        addNote,
        getNotes,
        
        // Geocoding
        geocode
    };
})();

// Global erişim için
window.API = API;


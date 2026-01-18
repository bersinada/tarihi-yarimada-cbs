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

    // ============================================
    // Assets API (Heritage Assets / Yapılar)
    // ============================================

    /**
     * Tüm yapıları getir
     * @param {object} params - { asset_type, historical_period, neighborhood, search, limit, offset }
     */
    async function getAssets(params = {}) {
        return get('/assets', params);
    }

    /**
     * Tek bir yapıyı getir (ID ile)
     */
    async function getAsset(id) {
        return get(`/assets/${id}`);
    }

    /**
     * Yapıları GeoJSON formatında getir
     * @param {object} params - { asset_type, historical_period, bbox }
     */
    async function getAssetsGeoJSON(params = {}) {
        return get('/assets/geojson', params);
    }

    /**
     * Yapı identifier ile getir (örn: HA-0001)
     */
    async function getAssetByIdentifier(identifier) {
        return get(`/assets/identifier/${identifier}`);
    }

    /**
     * Yapının aktörlerini getir (mimarlar, patronlar)
     */
    async function getAssetActors(assetId) {
        return get(`/assets/${assetId}/actors`);
    }

    /**
     * Yapının medyalarını getir
     */
    async function getAssetMedia(assetId) {
        return get(`/assets/${assetId}/media`);
    }

    /**
     * Yapı istatistiklerini getir
     */
    async function getAssetsStats() {
        return get('/assets/stats/summary');
    }

    // ============================================
    // Segments API (3D Model Parçaları)
    // ============================================

    /**
     * Tüm segmentleri getir
     * @param {object} params - { asset_id, segment_type, condition, limit, offset }
     */
    async function getSegments(params = {}) {
        return get('/segments', params);
    }

    /**
     * Tek bir segmenti getir
     */
    async function getSegment(segmentId) {
        return get(`/segments/${segmentId}`);
    }

    /**
     * Yapının segmentlerini getir
     */
    async function getAssetSegments(assetId, params = {}) {
        return get(`/segments/by-asset/${assetId}`, params);
    }

    /**
     * Segment tiplerini getir
     */
    async function getSegmentTypes() {
        return get('/segments/types');
    }

    /**
     * Segment istatistiklerini getir
     */
    async function getSegmentsStats() {
        return get('/segments/stats/summary');
    }

    // ============================================
    // Notes API (Kullanıcı Notları)
    // ============================================

    /**
     * Not ekle
     * @param {object} data - { asset_id, user_identifier, note_text }
     */
    async function addNote(data) {
        return post('/notes', data);
    }

    /**
     * Yapıya ait notları getir
     */
    async function getNotes(assetId) {
        return get(`/notes/by-asset/${assetId}`);
    }

    /**
     * Tüm notları getir
     * @param {object} params - { asset_id, user_identifier, limit, offset }
     */
    async function getAllNotes(params = {}) {
        return get('/notes', params);
    }

    /**
     * Tek bir notu getir
     */
    async function getNote(noteId) {
        return get(`/notes/${noteId}`);
    }

    /**
     * Notu sil
     */
    async function deleteNote(noteId) {
        return del(`/notes/${noteId}`);
    }

    // ============================================
    // Search & Metadata API
    // ============================================

    /**
     * Arama yap
     */
    async function search(query) {
        return get('/search', { q: query });
    }

    /**
     * Dataset metadata getir (ISO 19115)
     */
    async function getMetadata() {
        return get('/metadata');
    }

    // ============================================
    // Legacy/Uyumluluk fonksiyonları
    // (Eski kod için geriye dönük uyumluluk)
    // ============================================

    // Eski isimler - yeni fonksiyonlara yönlendir
    const getBuildings = getAssets;
    const getBuilding = getAsset;
    const getYapilar = getAssets;
    const getYapi = getAsset;

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
        
        // Assets (Heritage Assets / Yapılar)
        getAssets,
        getAsset,
        getAssetsGeoJSON,
        getAssetByIdentifier,
        getAssetActors,
        getAssetMedia,
        getAssetsStats,
        
        // Legacy/Uyumluluk (eski kod için)
        getBuildings,
        getBuilding,
        getYapilar,
        getYapi,
        
        // Segments (3D Model Parçaları)
        getSegments,
        getSegment,
        getAssetSegments,
        getSegmentTypes,
        getSegmentsStats,
        
        // Notes (Kullanıcı Notları)
        addNote,
        getNotes,
        getAllNotes,
        getNote,
        deleteNote,
        
        // Search & Metadata
        search,
        getMetadata
    };
})();

// Global erişim için
window.API = API;




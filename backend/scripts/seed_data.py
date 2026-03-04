"""
Tarihi Yarimada CBS - Database Seed Script
Populates the database with initial sample data

Data includes:
- 1 Dataset Metadata (ISO 19115)
- 3 Actors (architects/patrons)
- 5 Heritage Assets
- 6+ Asset Segments (SAM3D)
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# .env dosyasını yükle
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Backend klasöründeki .env'i dene
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()  # Mevcut dizinde .env ara

# Database URL'i al - önce local_database_url (küçük harf), sonra LOCAL_DATABASE_URL, sonra DATABASE_URL
database_url = (
    os.getenv("local_database_url") or 
    os.getenv("LOCAL_DATABASE_URL") or 
    os.getenv("DATABASE_URL") or
    os.getenv("AZURE_DATABASE_URL")
)

# Eğer local_database_url bulunduysa, DATABASE_URL'i de set et
# (database.py modülü DATABASE_URL bekliyor)
if database_url and not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = database_url

from sqlalchemy import text
from app.db.database import SessionLocal, engine, Base, init_db
from app.db.models import (
    HeritageAsset, AssetSegment, DatasetMetadata,
    Actor, AssetActor, Media, UserNote
)


def seed_database():
    """Seed the database with sample data"""
    print("Starting database seed process...")

    # Initialize database (create tables)
    init_db()

    db = SessionLocal()

    try:
        # Check if data already exists
        existing_assets = db.query(HeritageAsset).count()
        if existing_assets > 0:
            print(f"Database already contains {existing_assets} assets. Skipping seed.")
            return

        print("Seeding data...")

        # ==================================================
        # 1. Dataset Metadata (ISO 19115)
        # ==================================================
        print("  Adding dataset metadata...")
        metadata = DatasetMetadata(
            title="İstanbul Tarihi Yarımada Kültürel Miras Envanteri",
            abstract="İstanbul Tarihi Yarımada'daki tescilli kültürel miras yapılarının mekansal veritabanı. SAM3D segmentasyon ve Gaussian Splatting 3D model desteği.",
            purpose="Kültürel miras yapılarının 3D görselleştirmesi, segmentasyon analizi ve CBS tabanlı bilgi sistemi",
            language="tr",
            west_bound=28.916,
            east_bound=28.990,
            south_bound=40.996,
            north_bound=41.030,
            coordinate_system="EPSG:4326",
            lineage="Veriler Kültür ve Turizm Bakanlığı, İBB Açık Veri Portalı ve saha çalışmalarından derlenmiştir. 3D modeller SAM3D ve Gaussian Splatting teknikleriyle üretilmiştir.",
            spatial_resolution="Bina ve yapı elemanı düzeyi",
            distribution_format="GeoJSON, 3D Tiles, Gaussian Splat",
            license="CC BY-NC 4.0",
            contact_organization="Tarihi Yarımada CBS Projesi",
            metadata_standard="ISO 19115:2014"
        )
        db.add(metadata)

        # ==================================================
        # 2. Actors (Architects & Patrons)
        # ==================================================
        print("  Adding actors...")

        # Mimar Sinan
        sinan = Actor(
            identifier="AC-0001",
            name_tr="Mimar Sinan",
            name_en="Sinan the Architect",
            actor_type="architect",
            bio_tr="Osmanlı İmparatorluğu'nun en büyük mimarı. 400'den fazla yapı tasarlamıştır.",
            birth_year=1489,
            death_year=1588
        )
        db.add(sinan)

        # Kanuni Sultan Süleyman
        kanuni = Actor(
            identifier="AC-0002",
            name_tr="Kanuni Sultan Süleyman",
            name_en="Suleiman the Magnificent",
            actor_type="patron",
            bio_tr="Osmanlı İmparatorluğu'nun 10. padişahı. Pek çok önemli yapının banisidir.",
            birth_year=1494,
            death_year=1566
        )
        db.add(kanuni)

        # I. Justinianus
        justinian = Actor(
            identifier="AC-0003",
            name_tr="I. Justinianus",
            name_en="Justinian I",
            actor_type="patron",
            bio_tr="Bizans İmparatoru. Ayasofya'nın inşasını başlatan hükümdardır.",
            birth_year=482,
            death_year=565
        )
        db.add(justinian)

        db.flush()  # Get IDs for actors

        # ==================================================
        # 3. Heritage Assets (5 buildings)
        # ==================================================
        print("  Adding heritage assets...")

        # Süleymaniye Camii
        suleymaniye = HeritageAsset(
            identifier="HA-0001",
            name_tr="Süleymaniye Camii",
            name_en="Suleymaniye Mosque",
            asset_type="cami",
            construction_year=1557,
            construction_period="1550-1557",
            historical_period="osmanli_klasik",
            location="SRID=4326;POINT(28.9638 41.0162)",
            neighborhood="Süleymaniye",
            description_tr="Mimar Sinan'ın 'kalfalık eserim' dediği cami. Osmanlı mimarisinin en önemli yapılarından biri.",
            description_en="The mosque that Sinan called his 'journeyman work'. One of the most important structures of Ottoman architecture.",
            protection_status="1. derece",
            model_type="3DTILES",
            model_lod="LOD3",
            cesium_ion_asset_id=4357341,
            is_visitable=True,
            data_source="Kültür ve Turizm Bakanlığı"
        )
        db.add(suleymaniye)

        # Ayasofya
        ayasofya = HeritageAsset(
            identifier="HA-0002",
            name_tr="Ayasofya",
            name_en="Hagia Sophia",
            asset_type="cami",
            construction_year=537,
            construction_period="532-537",
            historical_period="bizans",
            location="SRID=4326;POINT(28.9799 41.0085)",
            neighborhood="Sultanahmet",
            description_tr="\"Kutsal Bilgelik\" anlamına gelen Ayasofya, İmparator Jüstinyen tarafından 537 yılında beş yıl gibi kısa bir sürede tamamlanan, mimarlık tarihinin en önemli katedrali ve kenti simgeleyen yapıdır. Bazilika ile merkezi kubbe planını birleştiren yenilikçi mimarisinde Efes ve Aspendos gibi antik kentlerden getirilen sütunlar kullanılmıştır. 1453’te Fatih Sultan Mehmet tarafından camiye çevrilen, bir dönem müze olarak hizmet veren ve 2020’de tekrar cami statüsüne kavuşan yapı; Bizans mozaikleri, Osmanlı hat levhaları ve Mimar Sinan’ın eklediği güçlendirici payandalarıyla medeniyetlerin buluşma noktasıdır.",
            description_en="Built as the largest cathedral of the Byzantine Empire, one of the most important structures in world architectural history.",
            protection_status="UNESCO",
            model_type="3DTILES",
            model_lod="LOD3",
            cesium_ion_asset_id=4357357,
            is_visitable=True,
            data_source="UNESCO Dünya Mirası"
        )
        db.add(ayasofya)

        # Sultanahmet Camii
        sultanahmet = HeritageAsset(
            identifier="HA-0003",
            name_tr="Sultanahmet Camii",
            name_en="Sultan Ahmed Mosque (Blue Mosque)",
            asset_type="cami",
            construction_year=1616,
            construction_period="1609-1616",
            historical_period="osmanli_klasik",
            location="SRID=4326;POINT(28.9767 41.0054)",
            neighborhood="Sultanahmet",
            description_tr="Sultan I. Ahmet tarafından 1609-1617 yılları arasında Mimar Sedefkâr Mehmet Ağa’ya yaptırılan cami, Ayasofya’nın tam karşısında Osmanlı mimarisinin ihtişamını sergilemek üzere yükseltilmiş bir set üzerine inşa edilmiştir. İç mekanında kullanılan 21.000’den fazla mavi renkli İznik çinisi ve renkli vitraylarından süzülen ışık nedeniyle dünya çapında \"Mavi Cami\" olarak tanınır. Tüm Osmanlı coğrafyasının tek altı minareli camisi olma özelliğini taşıyan yapı; türbe, medrese ve imarethaneden oluşan geniş bir külliyenin merkezidir.",
            description_en="Famous for its 6 minarets, also known as the 'Blue Mosque', an Ottoman-era mosque.",
            protection_status="1. derece",
            model_type="3DTILES",
            model_lod="LOD3",
            cesium_ion_asset_id=4373033,
            is_visitable=True,
            data_source="Kültür ve Turizm Bakanlığı"
        )
        db.add(sultanahmet)

        # Kariye Camii
        kariye = HeritageAsset(
            identifier="HA-0004",
            name_tr="Kariye Camii",
            name_en="Chora Church (Kariye Mosque)",
            asset_type="cami",
            construction_year=534,
            construction_period="534-1511",
            historical_period="bizans",
            location="SRID=4326;POINT(28.9390 41.0311)",
            neighborhood="Edirnekapı",
            description_tr="Bizans dönemi kilisesi. Dünyaca ünlü mozaik ve fresklerine sahip önemli bir kültürel miras yapısı.",
            description_en="Byzantine-era church. An important cultural heritage structure with world-famous mosaics and frescoes.",
            protection_status="UNESCO",
            model_type="3DTILES",
            model_lod="LOD3",
            cesium_ion_asset_id=4357343,
            is_visitable=True,
            data_source="UNESCO Dünya Mirası"
        )
        db.add(kariye)

        # Molla Hüsrev Camii
        molla_husrev = HeritageAsset(
            identifier="HA-0005",
            name_tr="Molla Hüsrev Camii",
            name_en="Molla Husrev Mosque",
            asset_type="cami",
            construction_year=1455,
            construction_period="1455",
            historical_period="osmanli_klasik",
            location="SRID=4326;POINT(28.9593 41.0146)",
            neighborhood="Fatih",
            description_tr="Osmanlı Devleti'nin ilk şeyhülislamlarından Molla Hüsrev tarafından yaptırılan cami.",
            description_en="Mosque built by Molla Husrev, one of the first Shaykh al-Islams of the Ottoman Empire.",
            protection_status="1. derece",
            model_type="3DTILES",
            model_lod="LOD3",
            cesium_ion_asset_id=4357344,
            is_visitable=True,
            data_source="Kültür ve Turizm Bakanlığı"
        )
        db.add(molla_husrev)

        # ==================================================
        # Sultanahmet Meydani Yapiları - Yeni Eklenenler
        # ==================================================

        # Firuzağa Camii
        firuzaga = HeritageAsset(
            identifier="HA-0006",
            name_tr="Firuzağa Camii",
            name_en="Firuzaga Mosque",
            asset_type="cami",
            construction_year=1491,
            construction_period="1491",
            historical_period="osmanli_erken",
            location="SRID=4326;POINT(28.9761 41.0078)",
            neighborhood="Sultanahmet",
            description_tr="Sultan II. Bayezid’in başhazinedarı Firuz Ağa tarafından 1491 yılında inşa ettirilen bu yapı, tek kubbeli cami tipinin erken dönem Osmanlı sanatındaki en zarif örneklerinden biri kabul edilir. Sultanahmet’te Divanyolu’nun köşesinde yer alan kare planlı ve kesme taş işçilikli cami, on iki kenarlı bir kasnak üzerine oturan basık bir kubbeye sahiptir. Giriş kapısı üzerindeki hatları ünlü hattat Şeyh Hamdullah tarafından yazılan eser, çevresindeki yapıların zamanla yıkılmasına rağmen özgün mimari ahengini korumaktadır.",
            description_en="Mosque built by Firuz Aga, the Chief Black Eunuch, during the reign of Fatih Sultan Mehmed.",
            protection_status="1. derece",
            model_type="3DTILES",
            model_lod="LOD3",
            cesium_ion_asset_id=4361716,
            is_visitable=True,
            data_source="Kültür ve Turizm Bakanlığı"
        )
        db.add(firuzaga)

        # Örme Dikilitaş (Obelisk of Constantine)
        orme_dikilitas = HeritageAsset(
            identifier="HA-0007",
            name_tr="Örme Dikilitaş",
            name_en="Walled Obelisk (Constantine Obelisk)",
            asset_type="anit",
            construction_year=None,
            construction_period="4. yüzyıl (tahmini)",
            historical_period="bizans",
            location="SRID=4326;POINT(28.9748 41.0054)",
            neighborhood="Sultanahmet",
            description_tr="Sultanahmet Meydanı’nın (Hipodrom) güneyinde yer alan ve 32 metre yüksekliğiyle meydanın en uzun anıtı olan yapı, kaba yontulmuş taşların örülmesiyle oluşturulmuştur. 10. yüzyılda İmparator VII. Konstantinos tarafından tamir ettirildiğinde üzeri zaferleri tasvir eden yaldızlı tunç plakalarla kaplanmış, ancak bu plakalar 1204’teki Haçlı istilası sırasında yağmalanmıştır. Kaidesindeki Grekçe kitabede anıtın heybeti Rodos Kolosu ile kıyaslanırken, Osmanlı döneminde yeniçerilerin hünerlerini sergilemek için bu sütuna tırmandıkları bilinmektedir.",
            description_en="One of three obelisks in the Hippodrome. Erected by Constantine VII. Its bronze plates were plundered during the Crusades.",
            protection_status="UNESCO",
            model_type="3DTILES",
            model_lod="LOD3",
            cesium_ion_asset_id=4361663,
            is_visitable=True,
            data_source="UNESCO Dünya Mirası"
        )
        db.add(orme_dikilitas)

        # Dikilitaş (Obelisk of Theodosius)
        dikilitas = HeritageAsset(
            identifier="HA-0008",
            name_tr="Dikilitaş",
            name_en="Obelisk of Theodosius",
            asset_type="anit",
            construction_year=-1450,
            construction_period="M.Ö. 1450",
            historical_period="bizans",
            location="SRID=4326;POINT(28.9754 41.0059)",
            neighborhood="Sultanahmet",
            description_tr="Aslen MÖ 15. yüzyılda Firavun III. Thutmose tarafından Mezopotamya zaferlerinin anısına Mısır’daki Karnak Tapınağı’nın önüne dikilen bu anıt, MS 390 yılında İmparator I. Theodosius tarafından İstanbul’a getirtilmiştir. Yaklaşık 200 ton ağırlığında kırmızı Asvan granitinden yapılan yekpare obeliskin dört yüzünde Firavun’un gücünü ve tanrılara bağlılığını anlatan hiyeroglifler yer alır. Mermer kaidesinde İmparator ve ailesini Hipodrom’daki etkinlikleri izlerken gösteren kabartmalar ile anıtın dikilme sürecini anlatan Latince ve Grekçe kitabeler bulunmaktadır.",
            description_en="A granite obelisk originally erected by Thutmose II in ancient Egypt, brought to Constantinople by Theodosius I in AD 390.",
            protection_status="UNESCO",
            model_type="3DTILES",
            model_lod="LOD3",
            cesium_ion_asset_id=4361661,
            is_visitable=True,
            data_source="UNESCO Dünya Mirası"
        )
        db.add(dikilitas)

        # Yılanlı Sütun (Serpent Column)
        yilanli_sutun = HeritageAsset(
            identifier="HA-0009",
            name_tr="Yılanlı Sütun",
            name_en="Serpent Column",
            asset_type="anit",
            construction_year=-479,
            construction_period="M.Ö. 479",
            historical_period="bizans",
            location="SRID=4326;POINT(28.9751 41.0056)",
            neighborhood="Sultanahmet",
            description_tr="İstanbul Sultanahmet Meydanı'nda (Hipodrom) yer alan Yılanlı Sütun, birbirine dolanmış üç piton yılanını tasvir eden ve kentin klasik döneminden günümüze ulaşabilen en eski büyük boyutlu bronz eserdir. MÖ 479'daki Platea Savaşı'nda Perslere karşı zafer kazanan 31 Yunan şehir devletinin bronz ganimetleri eritilerek yapılan anıt, aslen Delfi'deki Apollon Tapınağı'nın önüne dikilmiş , ardından MS 324 yılında İmparator I. Konstantin tarafından İstanbul'a getirilmiştir. Halk arasında şehri yılan, akrep ve böcek istilasına karşı koruyan büyülü bir tılsım olduğuna inanılan bu anıtın orijinalinde yer alan üç yılan başı 1700 yılına kadar sütunun üzerinde kalmış olsa da günümüzde kayıptır; ancak bu başlardan birine ait bir parça bugün İstanbul Arkeoloji Müzeleri’nde sergilenmektedir.",
            description_en="Ancient Greek bronze monument made to commemorate the victory at the Battle of Plataea. The column is formed by three intertwined serpents.",
            protection_status="UNESCO",
            model_type="3DTILES",
            model_lod="LOD3",
            cesium_ion_asset_id=4361660,
            is_visitable=True,
            data_source="UNESCO Dünya Mirası"
        )
        db.add(yilanli_sutun)

        # I. Ahmet Türbesi
        ahmet_turbesi = HeritageAsset(
            identifier="HA-0010",
            name_tr="I. Ahmet Türbesi",
            name_en="Tomb of Ahmed I",
            asset_type="turbe",
            construction_year=1619,
            construction_period="1617-1619",
            historical_period="osmanli_klasik",
            location="SRID=4326;POINT(28.9771 41.0070)",
            neighborhood="Sultanahmet",
            description_tr="Sultanahmet Camii’nin mimarı Sedefkâr Mehmed Ağa tarafından 1617-1619 yılları arasında inşa edilen türbe, dış cephesindeki mermer kaplaması ve kare planıyla dikkat çeker. İç mekanı en seçkin İznik çinileri, kalem işleri ve sedef kakmalı kapılarıyla süslü olan yapıda, Sultan I. Ahmet’in yanı sıra eşi Kösem Sultan, oğulları Genç Osman ve IV. Murad gibi isimlerle birlikte toplam 36 kişi metfundur. Yapı, Osmanlı hanedanının en güçlü figürlerini barındıran tarihi bir haziredir.",
            description_en="The tomb located in the courtyard of the Blue Mosque, where Ahmed I and his family are buried.",
            protection_status="1. derece",
            model_type="3DTILES",
            model_lod="LOD3",
            cesium_ion_asset_id=4361659,
            is_visitable=True,
            data_source="Kültür ve Turizm Bakanlığı"
        )
        db.add(ahmet_turbesi)

        # Aya İrini (Hagia Irene)
        aya_irini = HeritageAsset(
            identifier="HA-0011",
            name_tr="Aya İrini",
            name_en="Hagia Irene",
            asset_type="kilise",
            construction_year=548,
            construction_period="324-548",
            historical_period="bizans",
            location="SRID=4326;POINT(28.9810 41.0096)",
            neighborhood="Sultanahmet",
            description_tr="İstanbul’un Fatih ilçesinde, Topkapı Sarayı’nın birinci avlusunda yer alan Aya İrini, Bizans İmparatorluğu’nun inşa edilen ilk kilisesi ve Ayasofya’dan sonra şehrin en büyük ikinci Bizans kilisesidir. Kelime anlamı \"Kutsal Barış\" olan yapı, 6. yüzyılda İmparator Jüstinyen tarafından bazilika planında yeniden inşa edilmiş ve günümüze atrium (avlu) kısmını koruyarak ulaşabilen tek örnek olmuştur. İstanbul’un fethinden sonra camiye çevrilmeyerek silah deposu (Cebehane) olarak kullanılan yapı, 19. yüzyılda Osmanlı Devleti’nin ilk müzesine dönüştürülmüştür.",
            description_en="One of the oldest churches in Istanbul. A rare Byzantine church that was never converted into a mosque. Today it is used as a museum and concert hall.",
            protection_status="1. derece",
            model_type="3DTILES",
            model_lod="LOD3",
            cesium_ion_asset_id=4361658,
            is_visitable=True,
            data_source="Kültür ve Turizm Bakanlığı"
        )
        db.add(aya_irini)

        # Alman Çeşmesi
        alman_cesmesi = HeritageAsset(
            identifier="HA-0012",
            name_tr="Alman Çeşmesi",
            name_en="German Fountain",
            asset_type="cesme",
            construction_year=1901,
            construction_period="1898-1901",
            historical_period="osmanli_gec",
            location="SRID=4326;POINT(28.9766 41.0071)",
            neighborhood="Sultanahmet",
            description_tr="Alman İmparatoru II. Wilhelm'in 1898'deki İstanbul ziyaretinin anısına ve Osmanlı-Alman dostluğunun bir simgesi olarak yaptırılan yapı, 1901 yılında açılmıştır. Tasarımı bizzat İmparator’un bir deseni üzerine geliştirilen ve Neo-Bizanten üslupta inşa edilen çeşme, sekizgen bir plana ve somaki mermer sütunlar üzerine oturan bir kubbeye sahiptir. Tüm parçaları Berlin’de hazırlanıp gemiyle İstanbul’a getirilerek monte edilen eserin kubbe içi altın mozaiklerle, kemerleri ise II. Abdülhamid ve II. Wilhelm’in sembollerini içeren madalyonlarla süslüdür.",
            description_en="A Neo-Byzantine style fountain gifted by Germany to commemorate German Emperor Wilhelm II's visit to Istanbul.",
            protection_status="1. derece",
            model_type="3DTILES",
            model_lod="LOD3",
            cesium_ion_asset_id=4361657,
            is_visitable=True,
            data_source="Kültür ve Turizm Bakanlığı"
        )
        db.add(alman_cesmesi)

        # III. Ahmet Çeşmesi
        ahmet_cesmesi = HeritageAsset(
            identifier="HA-0013",
            name_tr="III. Ahmet Çeşmesi",
            name_en="Fountain of Ahmed III",
            asset_type="cesme",
            construction_year=1728,
            construction_period="1728",
            historical_period="osmanli_klasik",
            location="SRID=4326;POINT(28.9812 41.0082)",
            neighborhood="Sultanahmet",
            description_tr="Lale Devri’nin (1728-1729) en ihtişamlı sivil mimari örneği olan bu abidevi çeşme, Topkapı Sarayı’nın ana giriş kapısı önünde yer almaktadır. Klasik Osmanlı tarzı ile Batı’nın Barok etkilerini harmanlayan yapı, beş kubbeli çatısı ve meyve motifli zengin mermer kabartmalarıyla bir \"mücevher kutusuna\" benzetilir. Köşelerinde sebiller ve dört yüzünde çeşmeler bulunan eserin üzerindeki kasideler Şair Seyyid Vehbi’ye, ön yüzündeki tarih beyti ise bizzat hattat olan Sultan III. Ahmed’e aittir.",
            description_en="Located in front of the Imperial Gate of Topkapi Palace, one of the finest examples of Ottoman rococo style fountain. It is a symbol of the Tulip Era.",
            protection_status="1. derece",
            model_type="3DTILES",
            model_lod="LOD3",
            cesium_ion_asset_id=4365203,
            is_visitable=True,
            data_source="Kültür ve Turizm Bakanlığı"
        )
        db.add(ahmet_cesmesi)

        db.flush()  # Get IDs for assets

        # ==================================================
        # 4. Asset-Actor Relationships
        # ==================================================
        print("  Adding asset-actor relationships...")

        # Suleymaniye - Sinan (architect)
        db.add(AssetActor(asset_id=suleymaniye.id, actor_id=sinan.id, role="architect"))
        # Suleymaniye - Kanuni (patron)
        db.add(AssetActor(asset_id=suleymaniye.id, actor_id=kanuni.id, role="patron"))
        # Ayasofya - Justinian (patron)
        db.add(AssetActor(asset_id=ayasofya.id, actor_id=justinian.id, role="patron"))
        # Kariye - Justinian (patron)
        db.add(AssetActor(asset_id=kariye.id, actor_id=justinian.id, role="patron"))

        # ==================================================
        # 5. Asset Segments (SAM3D) - Basit örnekler
        # ==================================================
        print("  Adding asset segments...")

        # Ayasofya ana kubbe
        db.add(AssetSegment(
            asset_id=ayasofya.id,
            segment_name="Ana Kubbe",
            segment_type="dome",
            object_id="dome_main_001",
            material="Tuğla",
            height_m=55.6,
            width_m=31.87,
            condition="restored",
            description_tr="Yapıldığı dönemde dünyanın en büyük kubbesi."
        ))

        # Sultanahmet ana kubbe
        db.add(AssetSegment(
            asset_id=sultanahmet.id,
            segment_name="Ana Kubbe",
            segment_type="dome",
            object_id="dome_main_001",
            material="Kurşun kaplama",
            height_m=43.0,
            width_m=23.5,
            condition="restored",
            restoration_year=2017,
            description_tr="Altı yarım kubbe ile desteklenen ana kubbe."
        ))

        # ==================================================
        # 6. Media (Fotograflar)
        # ==================================================
        print("  Adding media...")

        # Gercek fotograflar images/assets/ klasorunde
        # Format: /images/assets/yapi-adi-numara.jpg

        # Ayasofya
        db.add(Media(
            asset_id=ayasofya.id,
            media_type="image",
            url="/images/assets/ayasofya-1.jpg",
            caption="Ayasofya",
            is_primary=True
        ))

        # Sultanahmet Camii
        db.add(Media(
            asset_id=sultanahmet.id,
            media_type="image",
            url="/images/assets/sultanahmet-1.jpg",
            caption="Sultanahmet Camii (Mavi Cami)",
            is_primary=True
        ))

        # Firuzağa Camii
        db.add(Media(
            asset_id=firuzaga.id,
            media_type="image",
            url="/images/assets/firuz-aga-camii-1.jpg",
            caption="Firuzağa Camii",
            is_primary=True
        ))

        # Örme Dikilitaş
        db.add(Media(
            asset_id=orme_dikilitas.id,
            media_type="image",
            url="/images/assets/orme-dikilitas-1.jpg",
            caption="Örme Dikilitaş (Konstantin Dikilitaşı)",
            is_primary=True
        ))

        # Dikilitaş (Theodosius)
        db.add(Media(
            asset_id=dikilitas.id,
            media_type="image",
            url="/images/assets/dikilitas-1.jpg",
            caption="Dikilitaş (Theodosius Dikilitaşı)",
            is_primary=True
        ))

        # Yılanlı Sütun
        db.add(Media(
            asset_id=yilanli_sutun.id,
            media_type="image",
            url="/images/assets/yilanli-sutun-1.jpg",
            caption="Yılanlı Sütun",
            is_primary=True
        ))

        # I. Ahmet Türbesi (Sultanahmet Türbesi)
        db.add(Media(
            asset_id=ahmet_turbesi.id,
            media_type="image",
            url="/images/assets/sultanahmet-turbesi-1.jpg",
            caption="I. Ahmet Türbesi",
            is_primary=True
        ))

        # Aya İrini
        db.add(Media(
            asset_id=aya_irini.id,
            media_type="image",
            url="/images/assets/aya-irini-1.jpg",
            caption="Aya İrini Kilisesi",
            is_primary=True
        ))

        # Alman Çeşmesi
        db.add(Media(
            asset_id=alman_cesmesi.id,
            media_type="image",
            url="/images/assets/alman-cesmesi-1.jpg",
            caption="Alman Çeşmesi",
            is_primary=True
        ))

        # III. Ahmet Çeşmesi
        db.add(Media(
            asset_id=ahmet_cesmesi.id,
            media_type="image",
            url="/images/assets/ucuncu-ahmet-cesmesi-1.jpg",
            caption="III. Ahmet Çeşmesi",
            is_primary=True
        ))

        db.commit()
        print("\nDatabase seed completed successfully!")

        # Print summary
        print("\nSummary:")
        print(f"  - Dataset Metadata: 1")
        print(f"  - Actors: {db.query(Actor).count()}")
        print(f"  - Heritage Assets: {db.query(HeritageAsset).count()}")
        print(f"  - Asset Segments: {db.query(AssetSegment).count()}")
        print(f"  - Asset-Actor Relations: {db.query(AssetActor).count()}")
        print(f"  - Media: {db.query(Media).count()}")

    except Exception as e:
        db.rollback()
        print(f"Error during seed: {e}")
        raise
    finally:
        db.close()


def clear_database():
    """Clear all data from the database (use with caution!)"""
    db = SessionLocal()
    try:
        print("Clearing database...")
        db.execute(text("DELETE FROM asset_actors"))
        db.execute(text("DELETE FROM asset_segments"))
        db.execute(text("DELETE FROM media"))
        db.execute(text("DELETE FROM user_notes"))
        db.execute(text("DELETE FROM heritage_assets"))
        db.execute(text("DELETE FROM actors"))
        db.execute(text("DELETE FROM dataset_metadata"))
        db.commit()
        print("Database cleared!")
    except Exception as e:
        db.rollback()
        print(f"Error clearing database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Database seed script")
    parser.add_argument("--clear", action="store_true", help="Clear database before seeding")
    args = parser.parse_args()

    if args.clear:
        clear_database()

    seed_database()

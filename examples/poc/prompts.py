"""60 realistic prompts across 4 categories for PoC benchmarking."""
from dataclasses import dataclass
from typing import List


@dataclass
class Prompt:
    id: str
    category: str  # qa | summarize | classify | generate
    text: str


PROMPTS: List[Prompt] = [
    # ── FACTUAL Q&A (15) ─────────────────────────────────────────
    Prompt("qa_01", "qa", "Apa ibu kota Indonesia? Jawab 1 kalimat."),
    Prompt("qa_02", "qa", "Sebutkan 3 planet terdekat ke Matahari."),
    Prompt("qa_03", "qa", "Siapa penemu bola lampu? Jawab singkat."),
    Prompt("qa_04", "qa", "Apa rumus luas lingkaran?"),
    Prompt("qa_05", "qa", "Tahun berapa Indonesia merdeka?"),
    Prompt("qa_06", "qa", "What is the boiling point of water in Celsius?"),
    Prompt("qa_07", "qa", "Sebutkan 3 bahasa pemrograman populer untuk web."),
    Prompt("qa_08", "qa", "Apa perbedaan RAM dan ROM? Maksimal 2 kalimat."),
    Prompt("qa_09", "qa", "Siapa presiden pertama Republik Indonesia?"),
    Prompt("qa_10", "qa", "Define photosynthesis in one sentence."),
    Prompt("qa_11", "qa", "Apa kepanjangan dari HTTP?"),
    Prompt("qa_12", "qa", "Sebutkan 2 manfaat olahraga rutin."),
    Prompt("qa_13", "qa", "Apa fungsi utama hati pada tubuh manusia?"),
    Prompt("qa_14", "qa", "What does CPU stand for?"),
    Prompt("qa_15", "qa", "Sebutkan 3 sumber energi terbarukan."),

    # ── SUMMARIZE (15) ───────────────────────────────────────────
    Prompt("sm_01", "summarize", "Ringkas dalam 1 kalimat: 'Hujan deras mengguyur Jakarta sejak pagi, menyebabkan banjir di beberapa titik. BMKG memprediksi cuaca ekstrem berlanjut hingga sore.'"),
    Prompt("sm_02", "summarize", "Ringkas: 'Tim sepak bola nasional menang 2-1 melawan Vietnam dalam pertandingan persahabatan. Gol dicetak oleh penyerang muda di babak kedua.'"),
    Prompt("sm_03", "summarize", "Summarize in 1 sentence: 'Apple announced its new iPhone with improved battery life and a faster processor. The device will be available next month in select markets.'"),
    Prompt("sm_04", "summarize", "Ringkas: 'Harga minyak dunia naik 3% setelah OPEC mengumumkan pemangkasan produksi. Analis memprediksi kenaikan akan berdampak pada harga BBM domestik.'"),
    Prompt("sm_05", "summarize", "Ringkas dalam 2 poin: 'Startup teknologi ABC meraih pendanaan Seri B sebesar $10 juta. Dana akan digunakan untuk ekspansi ke Asia Tenggara dan pengembangan produk baru berbasis AI.'"),
    Prompt("sm_06", "summarize", "TL;DR: 'Kebijakan baru pemerintah mewajibkan semua kendaraan listrik mendapat insentif pajak hingga 2027. Tujuannya mempercepat transisi energi bersih.'"),
    Prompt("sm_07", "summarize", "Summarize: 'Researchers found that 30 minutes of daily walking reduces heart disease risk by 25%. The study followed 50,000 adults over 10 years.'"),
    Prompt("sm_08", "summarize", "Ringkas: 'Gempa magnitudo 5.8 mengguncang wilayah selatan Jawa Barat. Tidak ada korban jiwa, namun beberapa rumah mengalami kerusakan ringan.'"),
    Prompt("sm_09", "summarize", "Ringkas 1 kalimat: 'Konser musik tahunan di Bali menarik 50 ribu pengunjung domestik dan internasional. Acara berlangsung selama 3 hari dengan 40 artis tampil.'"),
    Prompt("sm_10", "summarize", "Summarize: 'A new study suggests that drinking coffee in moderation may improve cognitive function in adults over 60. Results were published in a peer-reviewed journal.'"),
    Prompt("sm_11", "summarize", "Ringkas: 'Bank Indonesia menaikkan suku bunga acuan 25 basis poin untuk meredam inflasi. Keputusan ini disambut hati-hati oleh pelaku pasar.'"),
    Prompt("sm_12", "summarize", "Ringkas 2 poin: 'Pelaku UMKM di Yogyakarta mengeluhkan kenaikan harga bahan baku. Pemerintah daerah berjanji memberikan subsidi sementara untuk membantu kelangsungan usaha.'"),
    Prompt("sm_13", "summarize", "TL;DR: 'Tim peneliti Indonesia berhasil mengembangkan vaksin lokal untuk penyakit X. Uji klinis fase 3 sudah selesai dengan tingkat efikasi 89%.'"),
    Prompt("sm_14", "summarize", "Summarize in 1 line: 'Global temperatures hit record highs again this summer, with several regions experiencing prolonged heatwaves and wildfires.'"),
    Prompt("sm_15", "summarize", "Ringkas: 'Festival film internasional di Jakarta menampilkan 100 film dari 30 negara. Penghargaan film terbaik diberikan kepada karya sutradara muda Indonesia.'"),

    # ── CLASSIFY (15) ────────────────────────────────────────────
    Prompt("cl_01", "classify", "Klasifikasi sentimen (positif/negatif/netral): 'Pelayanan kasirnya ramah sekali, pulang dengan senang.'"),
    Prompt("cl_02", "classify", "Sentimen: 'Produk rusak saat diterima, tidak sesuai foto sama sekali.'"),
    Prompt("cl_03", "classify", "Sentimen: 'Pengiriman sesuai estimasi, barang aman.'"),
    Prompt("cl_04", "classify", "Classify (spam/not spam): 'CONGRATS! You won $1000, click this link now!!!'"),
    Prompt("cl_05", "classify", "Spam atau bukan: 'Rapat tim besok pukul 10 di ruang B.'"),
    Prompt("cl_06", "classify", "Kategori (teknologi/olahraga/politik/hiburan): 'Smartphone flagship terbaru dirilis dengan kamera 200MP.'"),
    Prompt("cl_07", "classify", "Kategori: 'Timnas voli putri lolos ke final SEA Games.'"),
    Prompt("cl_08", "classify", "Kategori: 'Presiden meresmikan jembatan baru di Sumatera.'"),
    Prompt("cl_09", "classify", "Kategori: 'Film horor ini meraih 1 juta penonton di minggu pertama.'"),
    Prompt("cl_10", "classify", "Intent (pertanyaan/keluhan/pujian): 'Kapan pesanan saya sampai? Sudah seminggu.'"),
    Prompt("cl_11", "classify", "Intent: 'Terima kasih, makanannya enak banget!'"),
    Prompt("cl_12", "classify", "Intent: 'Aplikasi error terus saat checkout, tolong perbaiki.'"),
    Prompt("cl_13", "classify", "Bahasa (id/en/jp): 'Selamat pagi semuanya'"),
    Prompt("cl_14", "classify", "Bahasa: 'Good morning everyone'"),
    Prompt("cl_15", "classify", "Bahasa: 'おはようございます'"),

    # ── GENERATE (15) ────────────────────────────────────────────
    Prompt("gn_01", "generate", "Tulis email singkat (3 kalimat) izin tidak masuk kerja karena sakit."),
    Prompt("gn_02", "generate", "Buatkan 1 paragraf deskripsi produk untuk kemeja batik premium."),
    Prompt("gn_03", "generate", "Write 3 catchy taglines for an organic coffee brand."),
    Prompt("gn_04", "generate", "Buat 5 ide nama startup di bidang edtech."),
    Prompt("gn_05", "generate", "Tulis caption Instagram (2 kalimat) untuk foto sunset di pantai."),
    Prompt("gn_06", "generate", "Buatkan jadwal harian sederhana untuk produktivitas (5 poin)."),
    Prompt("gn_07", "generate", "Tulis 1 paragraf motivasi singkat untuk pelajar."),
    Prompt("gn_08", "generate", "Write a polite reply declining a meeting invitation."),
    Prompt("gn_09", "generate", "Buat 3 pertanyaan interview untuk posisi backend engineer."),
    Prompt("gn_10", "generate", "Tulis pesan ucapan ulang tahun untuk teman dekat (2 kalimat)."),
    Prompt("gn_11", "generate", "Buatkan judul untuk artikel tentang manfaat AI di bidang kesehatan."),
    Prompt("gn_12", "generate", "Write a short product review (3 sentences) for a comfortable office chair."),
    Prompt("gn_13", "generate", "Buat 1 paragraf tentang pentingnya literasi keuangan."),
    Prompt("gn_14", "generate", "Tulis 5 manfaat tidur cukup, format bullet."),
    Prompt("gn_15", "generate", "Buat outline 3 poin untuk presentasi singkat tentang remote work."),
]


def get_prompts(n: int = None, category: str = None) -> List[Prompt]:
    pool = PROMPTS
    if category:
        pool = [p for p in pool if p.category == category]
    if n is not None and n < len(pool):
        pool = pool[:n]
    return pool

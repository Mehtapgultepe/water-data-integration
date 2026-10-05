import React, { useState, useEffect, useRef } from 'react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip 
} from 'recharts';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Droplets, TrendingUp, AlertTriangle, Calendar, Layers, MapPin } from 'lucide-react';

// İstanbul ve Trakya Barajlarının Gerçek Koordinatları (Hem Türkçe hem ASCII karakterler)
const DAM_COORDINATES = {
  // Türkçe karakterli isimler
  "Ömerli": [41.0536, 29.3567],
  "Darlık": [41.1417, 29.5750],
  "Elmalı": [41.0772, 29.1039],
  "Terkos": [41.3325, 28.5833],
  "Alibey": [41.1342, 28.9178],
  "Büyükçekmece": [41.0567, 28.5528],
  "Sazlıdere": [41.1214, 28.7303],
  "Istrancalar": [41.5283, 28.1633],
  "Kazandere": [41.5647, 28.0828],
  "Pabuçdere": [41.6039, 28.0683],

  // ASCII isimler
  "Omerli": [41.0536, 29.3567],
  "Darlik": [41.1417, 29.5750],
  "Elmali": [41.0772, 29.1039],
  "Buyukcekmece": [41.0567, 28.5528],
  "Sazlidere": [41.1214, 28.7303],
  "Pabucdere": [41.6039, 28.0683]
};

// Baraj seçildiğinde haritayı yumuşak şekilde oraya kaydıran yardımcı bileşen
function MapFlyTo({ selectedDam }) {
  const map = useMap();
  useEffect(() => {
    if (selectedDam && selectedDam.coords) {
      map.flyTo(selectedDam.coords, 10, {
        duration: 1.2
      });
    }
  }, [selectedDam, map]);
  return null;
}

export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedDam, setSelectedDam] = useState(null);
  
  const markerRefs = useRef({});

  useEffect(() => {
    fetch('/data.json')
      .then((res) => res.json())
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Veri yüklenemedi:", err);
        setLoading(false);
      });
  }, []);

  const handleSelectDam = (dam) => {
    setSelectedDam(dam);
    if (markerRefs.current[dam.name]) {
      markerRefs.current[dam.name].openPopup();
    }
  };

  const getMarkerColor = (rate) => {
    if (rate >= 70) return '#10b981'; // Yeşil (Yüksek)
    if (rate >= 40) return '#06b6d4'; // Turkuaz/Mavi (Orta)
    return '#f43f5e'; // Kırmızı (Kritik)
  };

  // Tarih formatını temizle (Örn: 2024-02-19T00:00:00 -> 19.02.2024)
  const formatDate = (rawDate) => {
    if (!rawDate) return '';
    const datePart = rawDate.split(' ')[0].split('T')[0];
    const parts = datePart.split('-');
    if (parts.length === 3) {
      return `${parts[2]}.${parts[1]}.${parts[0]}`;
    }
    return datePart;
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-cyan-400 font-sans">
        <Droplets className="h-8 w-8 animate-bounce mr-3" />
        <span className="text-xl font-medium">Dashboard ve Harita Yükleniyor...</span>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-rose-400 font-sans">
        <AlertTriangle className="h-8 w-8 mr-3" />
        <span>Veri yüklenemedi. public/data.json dosyasını kontrol edin.</span>
      </div>
    );
  }

  const cleanDateStr = formatDate(data.last_updated);

  // Baraj verilerine koordinat ekleme
  const damsWithCoords = (data.dam_bars || []).map((dam, index) => {
    const fallbackCoord = [41.15 + (index * 0.04), 28.75 + (index * 0.05)];
    return {
      ...dam,
      coords: DAM_COORDINATES[dam.name] || fallbackCoord
    };
  });

  const lowestRate = data.lowest_dam?.rate ?? 0;
  const lowestColor = getMarkerColor(lowestRate);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10 font-sans">
      {/* Üst Başlık */}
      <header className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <Droplets className="h-8 w-8 text-cyan-400" />
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
              İstanbul Baraj Doluluk & İzleme Platformu
            </h1>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            İBB Açık Veri Portalı & İSKİ Entegrasyonu • Coğrafi ve Analitik Raporlama
          </p>
        </div>
        <div className="flex items-center gap-2 bg-slate-900 px-4 py-2 rounded-lg border border-slate-800 text-xs text-slate-400 self-start md:self-auto">
          <Calendar className="h-4 w-4 text-cyan-400" />
          <span>Sistem Tarihi: {cleanDateStr}</span>
        </div>
      </header>

      {/* KPI Kartları */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        {/* 1. Genel Doluluk */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex justify-between items-center text-slate-400 mb-2">
            <span className="text-xs uppercase tracking-wider font-semibold">Genel Doluluk Oranı</span>
            <Droplets className="h-5 w-5 text-cyan-400" />
          </div>
          <div className="text-3xl font-extrabold text-cyan-400">%{data.general_average}</div>
          <div className="text-xs text-slate-400 mt-2">10 barajın ağırlıklı ortalaması</div>
        </div>

        {/* 2. En Yüksek Seviye */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex justify-between items-center text-slate-400 mb-2">
            <span className="text-xs uppercase tracking-wider font-semibold">En Yüksek Seviye</span>
            <TrendingUp className="h-5 w-5 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400">
            {data.highest_dam?.name}
          </div>
          <div className="text-xs text-slate-400 mt-2">
            Doluluk Oranı: %{data.highest_dam?.rate}
          </div>
        </div>

        {/* 3. En Düşük Seviye (Dinamik Renkli) */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex justify-between items-center text-slate-400 mb-2">
            <span className="text-xs uppercase tracking-wider font-semibold">En Düşük Seviye</span>
            <AlertTriangle className="h-5 w-5" style={{ color: lowestColor }} />
          </div>
          <div className="text-3xl font-extrabold" style={{ color: lowestColor }}>
            {data.lowest_dam?.name}
          </div>
          <div className="text-xs text-slate-400 mt-2">
            Doluluk Oranı: %{data.lowest_dam?.rate} {lowestRate >= 40 && '(Güvenli Bölgede)'}
          </div>
        </div>

        {/* 4. Aktif Baraj Sayısı */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex justify-between items-center text-slate-400 mb-2">
            <span className="text-xs uppercase tracking-wider font-semibold">Aktif Baraj Sayısı</span>
            <Layers className="h-5 w-5 text-indigo-400" />
          </div>
          <div className="text-3xl font-extrabold text-indigo-400">
            {damsWithCoords.length} Baraj
          </div>
          <div className="text-xs text-slate-400 mt-2">Harita üzerinde listelenen</div>
        </div>
      </div>

      {/* Harita ve Liste Izgarası */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        {/* İnteraktif Harita */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
            <div>
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <MapPin className="h-5 w-5 text-cyan-400" />
                İstanbul Su Havzaları Haritası
              </h2>
              <p className="text-xs text-slate-400">Baraj noktasına tıklayarak veya listeden seçerek konumu inceleyin</p>
            </div>
            {/* Lejant */}
            <div className="flex items-center gap-3 text-xs text-slate-400">
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> %70+</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-cyan-500"></span> %40-70</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Kritik (&lt;%40)</span>
            </div>
          </div>

          <div className="h-[380px] w-full rounded-lg overflow-hidden border border-slate-800 relative z-0">
            <MapContainer 
              center={[41.20, 28.95]} 
              zoom={8} 
              scrollWheelZoom={true} 
              style={{ height: '100%', width: '100%', background: '#090d16' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              
              <MapFlyTo selectedDam={selectedDam} />

              {damsWithCoords.map((dam) => {
                const isSelected = selectedDam?.name === dam.name;
                return (
                  <CircleMarker
                    key={dam.name}
                    ref={(el) => {
                      if (el) markerRefs.current[dam.name] = el;
                    }}
                    center={dam.coords}
                    radius={isSelected ? Math.max(14, dam.rate / 2.5) : Math.max(9, dam.rate / 3.5)}
                    pathOptions={{
                      color: isSelected ? '#ffffff' : getMarkerColor(dam.rate),
                      fillColor: getMarkerColor(dam.rate),
                      fillOpacity: isSelected ? 0.9 : 0.7,
                      weight: isSelected ? 3 : 2
                    }}
                    eventHandlers={{
                      click: () => handleSelectDam(dam)
                    }}
                  >
                    <Popup>
                      <div className="text-slate-900 p-1 font-sans min-w-[140px]">
                        <div className="font-bold text-sm border-b pb-1 text-slate-800">{dam.name} Barajı</div>
                        <div className="text-xs mt-1.5 flex justify-between">
                          <span className="text-slate-500">Doluluk:</span>
                          <strong className="text-cyan-700 font-bold">%{dam.rate}</strong>
                        </div>
                        <div className="text-[11px] mt-1 text-slate-400 flex items-center justify-between pt-1 border-t border-slate-100">
                          <span>Tarih:</span>
                          <span className="font-medium text-slate-600">{cleanDateStr}</span>
                        </div>
                      </div>
                    </Popup>
                  </CircleMarker>
                );
              })}
            </MapContainer>
          </div>
        </div>

        {/* Baraj Seçim Listesi */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-100 mb-1">Baraj Seviyeleri</h2>
            <p className="text-xs text-slate-400 mb-4">Haritada odaklanmak için bir baraja tıklayın</p>
            
            <div className="space-y-2 max-h-[290px] overflow-y-auto pr-1">
              {damsWithCoords.map((dam) => {
                const isSelected = selectedDam?.name === dam.name;
                return (
                  <div 
                    key={dam.name}
                    onClick={() => handleSelectDam(dam)}
                    className={`p-2.5 rounded-lg border transition-all cursor-pointer flex items-center justify-between ${
                      isSelected 
                        ? 'bg-slate-800 border-cyan-500 ring-2 ring-cyan-500/50 scale-[1.02]' 
                        : 'bg-slate-950/50 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <span 
                        className={`rounded-full transition-all ${isSelected ? 'w-3 h-3 ring-2 ring-white' : 'w-2.5 h-2.5'}`}
                        style={{ backgroundColor: getMarkerColor(dam.rate) }}
                      />
                      <span className={`text-sm ${isSelected ? 'font-bold text-cyan-200' : 'font-medium text-slate-200'}`}>
                        {dam.name}
                      </span>
                    </div>
                    <span className="text-sm font-bold" style={{ color: getMarkerColor(dam.rate) }}>
                      %{dam.rate}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
          
          {selectedDam && (
            <div className="mt-3 p-3 bg-cyan-950/40 border border-cyan-800/60 rounded-lg text-xs text-cyan-200 space-y-1">
              <div className="flex justify-between items-center">
                <span className="font-bold text-sm text-cyan-300">{selectedDam.name} Barajı</span>
                <span className="font-bold text-cyan-400">%{selectedDam.rate}</span>
              </div>
              <div className="flex items-center justify-between text-[11px] text-cyan-400/80 pt-1 border-t border-cyan-900/50">
                <span>Ölçüm Tarihi:</span>
                <strong>{cleanDateStr}</strong>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Alt Grafikler */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Trend Grafiği */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-100 mb-1">Tarihsel Değişim Trendi</h2>
          <p className="text-xs text-slate-400 mb-6">Son 30 günlük genel ortalama değişimi</p>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.timeseries}>
                <defs>
                  <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.4} />
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickFormatter={(val) => formatDate(val)} />
                <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 100]} unit="%" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  itemStyle={{ color: '#38bdf8' }}
                  labelFormatter={(val) => formatDate(val)}
                />
                <Area 
                  type="monotone" 
                  dataKey="val" 
                  name="Genel Ortalama"
                  stroke="#06b6d4" 
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#colorVal)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Baraj Dağılım Grafiği */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-100 mb-1">Baraj Sıralaması</h2>
          <p className="text-xs text-slate-400 mb-6">Doluluk seviyesi karşılaştırması</p>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart 
                layout="vertical"
                data={data.dam_bars}
                margin={{ left: 10, right: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} horizontal={false} />
                <XAxis type="number" stroke="#94a3b8" fontSize={11} domain={[0, 100]} unit="%" />
                <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={11} width={80} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  itemStyle={{ color: '#38bdf8' }}
                />
                <Bar dataKey="rate" name="Doluluk" fill="#38bdf8" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
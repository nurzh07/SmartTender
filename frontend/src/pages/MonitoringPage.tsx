import { useState, useEffect } from "react";
import {
  getExternalTenders,
  addToWatchlist,
  getWatchlist,
  removeFromWatchlist,
  getMonitoringCategories,
  getMonitoringRegions,
} from "../api";

export default function MonitoringPage() {
  const [tenders, setTenders] = useState<any[]>([]);
  const [watchlist, setWatchlist] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [regions, setRegions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    category: "",
    region: "",
    min_price: undefined as number | undefined,
    max_price: undefined as number | undefined,
  });

  useEffect(() => {
    loadTenders();
    loadWatchlist();
    loadCategories();
    loadRegions();
  }, []);

  const loadTenders = async () => {
    setLoading(true);
    try {
      const data = await getExternalTenders(filters);
      setTenders(data.tenders || []);
    } catch (error) {
      console.error("Failed to load tenders:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadWatchlist = async () => {
    try {
      const data = await getWatchlist();
      setWatchlist(data.watchlist || []);
    } catch (error) {
      console.error("Failed to load watchlist:", error);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await getMonitoringCategories();
      setCategories(data.categories || []);
    } catch (error) {
      console.error("Failed to load categories:", error);
    }
  };

  const loadRegions = async () => {
    try {
      const data = await getMonitoringRegions();
      setRegions(data.regions || []);
    } catch (error) {
      console.error("Failed to load regions:", error);
    }
  };

  const handleAddToWatchlist = async (tenderId: string, source: string) => {
    try {
      await addToWatchlist(tenderId, source);
      loadWatchlist();
      alert("Тендер бақылау тізіміне қосылды!");
    } catch (error) {
      console.error("Failed to add to watchlist:", error);
      alert("Қате орын алды!");
    }
  };

  const handleRemoveFromWatchlist = async (watchlistId: number) => {
    try {
      await removeFromWatchlist(watchlistId);
      loadWatchlist();
      alert("Тендер бақылау тізімінен өшірілді!");
    } catch (error) {
      console.error("Failed to remove from watchlist:", error);
      alert("Қате орын алды!");
    }
  };

  const isInWatchlist = (tenderId: string) => {
    return watchlist.some((item) => item.tender_id === tenderId);
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="page-title">Тендер мониторингі</h1>
        <p className="page-sub">Сыртқы тендерлерді бақылау (Goszakupki.kz, Samruk-Kazyna)</p>
      </div>

      {/* Фильтрлер */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div>
            <label className="label">Категория</label>
            <select
              className="input"
              value={filters.category}
              onChange={(e) => setFilters({ ...filters, category: e.target.value })}
            >
              <option value="">Барлық категориялар</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Аймақ</label>
            <select
              className="input"
              value={filters.region}
              onChange={(e) => setFilters({ ...filters, region: e.target.value })}
            >
              <option value="">Барлық аймақтар</option>
              {regions.map((reg) => (
                <option key={reg.id} value={reg.id}>
                  {reg.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Мин. баға</label>
            <input
              type="number"
              className="input"
              value={filters.min_price || ""}
              onChange={(e) => setFilters({ ...filters, min_price: e.target.value ? Number(e.target.value) : undefined })}
              placeholder="0"
            />
          </div>
          <div>
            <label className="label">Макс. баға</label>
            <input
              type="number"
              className="input"
              value={filters.max_price || ""}
              onChange={(e) => setFilters({ ...filters, max_price: e.target.value ? Number(e.target.value) : undefined })}
              placeholder="∞"
            />
          </div>
          <div className="flex items-end">
            <button className="btn btn-primary w-full" onClick={loadTenders}>
              Іздеу
            </button>
          </div>
        </div>
      </div>

      {/* Бақылау тізімі */}
      <div className="card mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="section-title">Бақылау тізімі ({watchlist.length})</h2>
        </div>
        {watchlist.length === 0 ? (
          <p className="empty-text">Бақылау тізімі бос</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Тендер ID</th>
                  <th>Көзі</th>
                  <th>Қосылған күні</th>
                  <th>Әрекет</th>
                </tr>
              </thead>
              <tbody>
                {watchlist.map((item) => (
                  <tr key={item.id}>
                    <td>{item.tender_id}</td>
                    <td>{item.source}</td>
                    <td>{new Date(item.created_at).toLocaleDateString("kk-KZ")}</td>
                    <td>
                      <button
                        className="btn btn-sm btn-danger"
                        onClick={() => handleRemoveFromWatchlist(item.id)}
                      >
                        Өшіру
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Тендер тізімі */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="section-title">Сыртқы тендерлер ({tenders.length})</h2>
        </div>
        {loading ? (
          <div className="flex justify-center items-center py-8">
            <div className="text-muted">Жүктелуде...</div>
          </div>
        ) : tenders.length === 0 ? (
          <p className="empty-text">Тендерлер табылмады</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Атауы</th>
                  <th>Бағасы</th>
                  <th>Категория</th>
                  <th>Аймақ</th>
                  <th>Дедлайн</th>
                  <th>Көзі</th>
                  <th>Әрекет</th>
                </tr>
              </thead>
              <tbody>
                {tenders.map((tender) => (
                  <tr key={tender.id}>
                    <td>
                      <div>
                        <div className="font-semibold">{tender.title}</div>
                        <div className="text-muted text-sm mt-1">
                          {tender.description?.substring(0, 100)}...
                        </div>
                      </div>
                    </td>
                    <td>
                      {tender.price?.toLocaleString()} {tender.currency}
                    </td>
                    <td>{tender.category}</td>
                    <td>{tender.region}</td>
                    <td>{tender.deadline ? new Date(tender.deadline).toLocaleDateString("kk-KZ") : "-"}</td>
                    <td>
                      <span className={`badge ${tender.source === "goszakupki" ? "badge-published" : "badge-awarded"}`}>
                        {tender.source === "goszakupki" ? "Goszakupki" : "Samruk-Kazyna"}
                      </span>
                    </td>
                    <td>
                      {isInWatchlist(tender.id) ? (
                        <button className="btn btn-sm btn-secondary" disabled>
                          ✓ Бақылауда
                        </button>
                      ) : (
                        <button
                          className="btn btn-sm btn-outline-primary"
                          onClick={() => handleAddToWatchlist(tender.id, tender.source)}
                        >
                          + Бақылау
                        </button>
                      )}
                      {tender.url && (
                        <a
                          href={tender.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn btn-sm btn-primary ml-2"
                        >
                          Ашу
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

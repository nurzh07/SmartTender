import { useState, useEffect } from "react";
import {
  createRating,
  getSupplierRatings,
  getSupplierAverageRating,
  createPortfolio,
  getMyPortfolio,
  updatePortfolio,
  deletePortfolio,
  createCertification,
  getMyCertifications,
  deleteCertification,
  getTenders,
  getUsers,
} from "../api";
import { useAuth } from "../context/AuthContext";

export function RatingsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<"ratings" | "portfolio" | "certifications">("ratings");
  
  // Ratings state
  const [supplierId, setSupplierId] = useState<number | "">("");
  const [tenderId, setTenderId] = useState<number | "">("");
  const [qualityScore, setQualityScore] = useState(5);
  const [deliveryScore, setDeliveryScore] = useState(5);
  const [communicationScore, setCommunicationScore] = useState(5);
  const [priceScore, setPriceScore] = useState(5);
  const [review, setReview] = useState("");
  const [ratings, setRatings] = useState<any[]>([]);
  const [averageRating, setAverageRating] = useState<any>(null);
  const [tenders, setTenders] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  
  // Portfolio state
  const [portfolio, setPortfolio] = useState<any[]>([]);
  const [portfolioForm, setPortfolioForm] = useState({
    id: null as number | null,
    project_name: "",
    project_description: "",
    project_value: "",
    completion_date: "",
    client_name: "",
    client_contact: "",
    documents: "",
  });
  const [showPortfolioModal, setShowPortfolioModal] = useState(false);
  
  // Certifications state
  const [certifications, setCertifications] = useState<any[]>([]);
  const [certificationForm, setCertificationForm] = useState({
    certification_name: "",
    issuing_organization: "",
    certificate_number: "",
    issue_date: "",
    expiry_date: "",
    document_url: "",
  });
  const [showCertificationModal, setShowCertificationModal] = useState(false);
  
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user?.role === "supplier") {
      loadMyPortfolio();
      loadMyCertifications();
    } else {
      loadTenders();
      loadUsers();
    }
  }, [user]);

  const loadTenders = async () => {
    try {
      const data = await getTenders();
      setTenders(data);
    } catch (error) {
      console.error("Failed to load tenders:", error);
    }
  };

  const loadUsers = async () => {
    try {
      const data = await getUsers();
      setUsers(data.filter((u: any) => u.role === "supplier"));
    } catch (error) {
      console.error("Failed to load users:", error);
    }
  };

  const loadRatings = async () => {
    if (!supplierId) return;
    try {
      const data = await getSupplierRatings(supplierId);
      setRatings(data.ratings || []);
    } catch (error) {
      console.error("Failed to load ratings:", error);
    }
  };

  const loadAverageRating = async () => {
    if (!supplierId) return;
    try {
      const data = await getSupplierAverageRating(supplierId);
      setAverageRating(data);
    } catch (error) {
      console.error("Failed to load average rating:", error);
    }
  };

  const handleSupplierChange = (id: number) => {
    setSupplierId(id);
    loadRatings();
    loadAverageRating();
  };

  const handleSubmitRating = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!supplierId || !tenderId) {
      alert("Жеткізуші және тендерді таңдаңыз");
      return;
    }
    setLoading(true);
    try {
      await createRating({
        tender_id: tenderId,
        supplier_id: supplierId,
        quality_score: qualityScore,
        delivery_score: deliveryScore,
        communication_score: communicationScore,
        price_score: priceScore,
        review: review,
      });
      alert("Рейтинг қосылды!");
      loadRatings();
      loadAverageRating();
      setTenderId("");
      setQualityScore(5);
      setDeliveryScore(5);
      setCommunicationScore(5);
      setPriceScore(5);
      setReview("");
    } catch (error) {
      console.error("Failed to create rating:", error);
      alert("Қате орын алды!");
    } finally {
      setLoading(false);
    }
  };

  const loadMyPortfolio = async () => {
    try {
      const data = await getMyPortfolio();
      setPortfolio(data.portfolio || []);
    } catch (error) {
      console.error("Failed to load portfolio:", error);
    }
  };

  const handlePortfolioSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (portfolioForm.id) {
        await updatePortfolio(portfolioForm.id, portfolioForm);
        alert("Портфолио жаңартылды!");
      } else {
        await createPortfolio(portfolioForm);
        alert("Портфолио қосылды!");
      }
      loadMyPortfolio();
      setShowPortfolioModal(false);
      setPortfolioForm({
        id: null,
        project_name: "",
        project_description: "",
        project_value: "",
        completion_date: "",
        client_name: "",
        client_contact: "",
        documents: "",
      });
    } catch (error) {
      console.error("Failed to save portfolio:", error);
      alert("Қате орын алды!");
    } finally {
      setLoading(false);
    }
  };

  const handleEditPortfolio = (item: any) => {
    setPortfolioForm({
      id: item.id,
      project_name: item.project_name,
      project_description: item.project_description || "",
      project_value: item.project_value?.toString() || "",
      completion_date: item.completion_date?.split("T")[0] || "",
      client_name: item.client_name || "",
      client_contact: item.client_contact || "",
      documents: item.documents || "",
    });
    setShowPortfolioModal(true);
  };

  const handleDeletePortfolio = async (id: number) => {
    if (!confirm("Сіз сенімдісіз бе?")) return;
    try {
      await deletePortfolio(id);
      alert("Портфолио өшірілді!");
      loadMyPortfolio();
    } catch (error) {
      console.error("Failed to delete portfolio:", error);
      alert("Қате орын алды!");
    }
  };

  const loadMyCertifications = async () => {
    try {
      const data = await getMyCertifications();
      setCertifications(data.certifications || []);
    } catch (error) {
      console.error("Failed to load certifications:", error);
    }
  };

  const handleCertificationSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createCertification(certificationForm);
      alert("Сертификат қосылды!");
      loadMyCertifications();
      setShowCertificationModal(false);
      setCertificationForm({
        certification_name: "",
        issuing_organization: "",
        certificate_number: "",
        issue_date: "",
        expiry_date: "",
        document_url: "",
      });
    } catch (error) {
      console.error("Failed to create certification:", error);
      alert("Қате орын алды!");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCertification = async (id: number) => {
    if (!confirm("Сіз сенімдісіз бе?")) return;
    try {
      await deleteCertification(id);
      alert("Сертификат өшірілді!");
      loadMyCertifications();
    } catch (error) {
      console.error("Failed to delete certification:", error);
      alert("Қате орын алды!");
    }
  };

  const renderStars = (score: number) => {
    let stars = "";
    for (let i = 1; i <= 5; i++) {
      stars += i <= score ? "★" : "☆";
    }
    return stars;
  };

  const isSupplier = user?.role === "supplier";

  return (
    <div>
      <div className="mb-6">
        <h1 className="page-title">Рейтинг жүйесі</h1>
        <p className="page-sub">Жеткізушілерді бағалау және портфолионы басқару</p>
      </div>

      {/* Tabs */}
      <ul className="nav-tabs">
        <li className="nav-item">
          <button
            className={activeTab === "ratings" ? "active" : ""}
            onClick={() => setActiveTab("ratings")}
          >
            {isSupplier ? "Менің рейтингім" : "Рейтингтер"}
          </button>
        </li>
        {isSupplier && (
          <>
            <li className="nav-item">
              <button
                className={activeTab === "portfolio" ? "active" : ""}
                onClick={() => setActiveTab("portfolio")}
              >
                Портфолио
              </button>
            </li>
            <li className="nav-item">
              <button
                className={activeTab === "certifications" ? "active" : ""}
                onClick={() => setActiveTab("certifications")}
              >
                Сертификаттар
              </button>
            </li>
          </>
        )}
      </ul>

      {/* Ratings Tab */}
      {activeTab === "ratings" && (
        <div>
          {!isSupplier ? (
            <>
              {/* Select Supplier */}
              <div className="card mb-6">
                <div className="mb-4">
                  <h2 className="section-title">Жеткізушіні таңдау</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2">
                  <div>
                    <label className="label">Жеткізуші</label>
                    <select
                      className="form-select"
                      value={supplierId}
                      onChange={(e) => handleSupplierChange(parseInt(e.target.value))}
                    >
                      <option value="">Жеткізушін таңдаңыз</option>
                      {users.map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.full_name || u.email}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Average Rating */}
              {averageRating && supplierId && (
                <div className="card mb-6">
                  <div className="mb-4">
                    <h2 className="section-title">Орташа рейтинг</h2>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="text-center">
                      <div className="display-4 text-primary">{averageRating.average?.toFixed(1)}</div>
                      <div className="stars-display justify-center mt-2">
                        {renderStars(Math.round(averageRating.average || 0))}
                      </div>
                      <div className="text-muted text-sm mt-1">{averageRating.total} рейтинг</div>
                    </div>
                    <div>
                      <div className="mb-3">
                        <strong>Сапасы:</strong> {averageRating.quality?.toFixed(1)} {renderStars(Math.round(averageRating.quality || 0))}
                      </div>
                      <div className="mb-3">
                        <strong>Жеткізу:</strong> {averageRating.delivery?.toFixed(1)} {renderStars(Math.round(averageRating.delivery || 0))}
                      </div>
                      <div className="mb-3">
                        <strong>Коммуникация:</strong> {averageRating.communication?.toFixed(1)} {renderStars(Math.round(averageRating.communication || 0))}
                      </div>
                      <div>
                        <strong>Баға:</strong> {averageRating.price?.toFixed(1)} {renderStars(Math.round(averageRating.price || 0))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Add Rating Form */}
              {supplierId && (
                <div className="card mb-6">
                  <div className="mb-4">
                    <h2 className="section-title">Рейтинг қосу</h2>
                  </div>
                  <form onSubmit={handleSubmitRating}>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div>
                        <label className="label">Тендер</label>
                        <select
                          className="form-select"
                          value={tenderId}
                          onChange={(e) => setTenderId(parseInt(e.target.value))}
                          required
                        >
                          <option value="">Тендерді таңдаңыз</option>
                          {tenders.map((t) => (
                            <option key={t.id} value={t.id}>
                              {t.title}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                      <div>
                        <label className="label">Сапасы ({qualityScore})</label>
                        <input
                          type="range"
                          className="form-range"
                          min="1"
                          max="5"
                          value={qualityScore}
                          onChange={(e) => setQualityScore(parseInt(e.target.value))}
                        />
                        <div className="text-muted text-sm">{renderStars(qualityScore)}</div>
                      </div>
                      <div>
                        <label className="label">Жеткізу ({deliveryScore})</label>
                        <input
                          type="range"
                          className="form-range"
                          min="1"
                          max="5"
                          value={deliveryScore}
                          onChange={(e) => setDeliveryScore(parseInt(e.target.value))}
                        />
                        <div className="text-muted text-sm">{renderStars(deliveryScore)}</div>
                      </div>
                      <div>
                        <label className="label">Коммуникация ({communicationScore})</label>
                        <input
                          type="range"
                          className="form-range"
                          min="1"
                          max="5"
                          value={communicationScore}
                          onChange={(e) => setCommunicationScore(parseInt(e.target.value))}
                        />
                        <div className="text-muted text-sm">{renderStars(communicationScore)}</div>
                      </div>
                      <div>
                        <label className="label">Баға ({priceScore})</label>
                        <input
                          type="range"
                          className="form-range"
                          min="1"
                          max="5"
                          value={priceScore}
                          onChange={(e) => setPriceScore(parseInt(e.target.value))}
                        />
                        <div className="text-muted text-sm">{renderStars(priceScore)}</div>
                      </div>
                    </div>
                    <div className="mb-4">
                      <label className="label">Пікір</label>
                      <textarea
                        className="form-textarea"
                        rows={3}
                        value={review}
                        onChange={(e) => setReview(e.target.value)}
                      />
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={loading}>
                      {loading ? "Жүктелуде..." : "Рейтинг қосу"}
                    </button>
                  </form>
                </div>
              )}

              {/* Ratings List */}
              {supplierId && (
                <div className="card">
                  <div className="mb-4">
                    <h2 className="section-title">Рейтингтер тізімі ({ratings.length})</h2>
                  </div>
                  {ratings.length === 0 ? (
                    <p className="empty-text">Рейтингтер жоқ</p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>Тендер</th>
                            <th>Сапасы</th>
                            <th>Жеткізу</th>
                            <th>Коммуникация</th>
                            <th>Баға</th>
                            <th>Орташа</th>
                            <th>Пікір</th>
                            <th>Күні</th>
                          </tr>
                        </thead>
                        <tbody>
                          {ratings.map((r) => (
                            <tr key={r.id}>
                              <td>{r.tender_title || r.tender_id}</td>
                              <td>{renderStars(r.quality_score)}</td>
                              <td>{renderStars(r.delivery_score)}</td>
                              <td>{renderStars(r.communication_score)}</td>
                              <td>{renderStars(r.price_score)}</td>
                              <td>{((r.quality_score + r.delivery_score + r.communication_score + r.price_score) / 4).toFixed(1)}</td>
                              <td>{r.review || "-"}</td>
                              <td>{new Date(r.created_at).toLocaleDateString("kk-KZ")}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <p className="empty-text">Сіздің рейтингіңіз әзірге қосылмады. Сатып алушылар сізді бағалай алады.</p>
          )}
        </div>
      )}

      {/* Portfolio Tab */}
      {activeTab === "portfolio" && isSupplier && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="section-title">Портфолио</h2>
            <button
              className="btn btn-primary"
              onClick={() => {
                setPortfolioForm({
                  id: null,
                  project_name: "",
                  project_description: "",
                  project_value: "",
                  completion_date: "",
                  client_name: "",
                  client_contact: "",
                  documents: "",
                });
                setShowPortfolioModal(true);
              }}
            >
              + Жаңа жоба қосу
            </button>
          </div>

          {portfolio.length === 0 ? (
            <div className="card">
              <div className="text-center py-8">
                <p className="empty-text">Портфолио бос</p>
              </div>
            </div>
          ) : (
            <div className="portfolio-grid">
              {portfolio.map((item) => (
                <div key={item.id} className="portfolio-card">
                  <div className="portfolio-title">{item.project_name}</div>
                  {item.project_description && (
                    <div className="portfolio-desc">{item.project_description}</div>
                  )}
                  {item.project_value && (
                    <div className="portfolio-meta">
                      <strong>Бағасы:</strong> {item.project_value.toLocaleString()}
                    </div>
                  )}
                  {item.completion_date && (
                    <div className="portfolio-meta">
                      <strong>Аяқталған күні:</strong> {new Date(item.completion_date).toLocaleDateString("kk-KZ")}
                    </div>
                  )}
                  {item.client_name && (
                    <div className="portfolio-meta">
                      <strong>Клиент:</strong> {item.client_name}
                    </div>
                  )}
                  {item.client_contact && (
                    <div className="portfolio-meta">
                      <strong>Контакт:</strong> {item.client_contact}
                    </div>
                  )}
                  <div className="mt-4 flex gap-2">
                    <button
                      className="btn btn-sm btn-outline-primary"
                      onClick={() => handleEditPortfolio(item)}
                    >
                      Өңдеу
                    </button>
                    <button
                      className="btn btn-sm btn-outline-danger"
                      onClick={() => handleDeletePortfolio(item.id)}
                    >
                      Өшіру
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Certifications Tab */}
      {activeTab === "certifications" && isSupplier && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="section-title">Сертификаттар</h2>
            <button
              className="btn btn-primary"
              onClick={() => setShowCertificationModal(true)}
            >
              + Сертификат қосу
            </button>
          </div>

          {certifications.length === 0 ? (
            <div className="card">
              <div className="text-center py-8">
                <p className="empty-text">Сертификаттар жоқ</p>
              </div>
            </div>
          ) : (
            <div className="portfolio-grid">
              {certifications.map((item) => (
                <div key={item.id} className="portfolio-card">
                  <div className="portfolio-title">{item.certification_name}</div>
                  <div className="portfolio-meta">
                    <strong>Берген ұйым:</strong> {item.issuing_organization}
                  </div>
                  {item.certificate_number && (
                    <div className="portfolio-meta">
                      <strong>Нөмірі:</strong> {item.certificate_number}
                    </div>
                  )}
                  {item.issue_date && (
                    <div className="portfolio-meta">
                      <strong>Берілген күні:</strong> {new Date(item.issue_date).toLocaleDateString("kk-KZ")}
                    </div>
                  )}
                  {item.expiry_date && (
                    <div className="portfolio-meta">
                      <strong>Аяқталған күні:</strong> {new Date(item.expiry_date).toLocaleDateString("kk-KZ")}
                    </div>
                  )}
                  {item.document_url && (
                    <div className="portfolio-meta">
                      <a href={item.document_url} target="_blank" rel="noopener noreferrer">
                        📄 Құжатты ашу
                      </a>
                    </div>
                  )}
                  <div className="mt-4">
                    <button
                      className="btn btn-sm btn-outline-danger"
                      onClick={() => handleDeleteCertification(item.id)}
                    >
                      Өшіру
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Portfolio Modal */}
      {showPortfolioModal && (
        <div className="modal-overlay" onClick={() => setShowPortfolioModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">{portfolioForm.id ? "Жобаны өңдеу" : "Жаңа жоба"}</div>
              <button
                className="btn btn-outline-secondary"
                onClick={() => setShowPortfolioModal(false)}
              >
                ✕
              </button>
            </div>
            <form onSubmit={handlePortfolioSubmit}>
              <div className="mb-4">
                <label className="label">Жоба атауы *</label>
                <input
                  type="text"
                  className="input"
                  value={portfolioForm.project_name}
                  onChange={(e) => setPortfolioForm({ ...portfolioForm, project_name: e.target.value })}
                  required
                />
              </div>
              <div className="mb-4">
                <label className="label">Сипаттама</label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  value={portfolioForm.project_description}
                  onChange={(e) => setPortfolioForm({ ...portfolioForm, project_description: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="label">Жоба бағасы</label>
                  <input
                    type="number"
                    className="input"
                    value={portfolioForm.project_value}
                    onChange={(e) => setPortfolioForm({ ...portfolioForm, project_value: e.target.value })}
                  />
                </div>
                <div>
                  <label className="label">Аяқталған күні</label>
                  <input
                    type="date"
                    className="input"
                    value={portfolioForm.completion_date}
                    onChange={(e) => setPortfolioForm({ ...portfolioForm, completion_date: e.target.value })}
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="label">Клиент аты</label>
                  <input
                    type="text"
                    className="input"
                    value={portfolioForm.client_name}
                    onChange={(e) => setPortfolioForm({ ...portfolioForm, client_name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="label">Клиенттің байланысы</label>
                  <input
                    type="text"
                    className="input"
                    value={portfolioForm.client_contact}
                    onChange={(e) => setPortfolioForm({ ...portfolioForm, client_contact: e.target.value })}
                  />
                </div>
              </div>
              <div className="mb-4">
                <label className="label">Құжаттар сілтемесі</label>
                <input
                  type="text"
                  className="input"
                  value={portfolioForm.documents}
                  onChange={(e) => setPortfolioForm({ ...portfolioForm, documents: e.target.value })}
                />
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowPortfolioModal(false)}
                >
                  Жабу
                </button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? "Жүктелуде..." : "Сақтау"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Certification Modal */}
      {showCertificationModal && (
        <div className="modal-overlay" onClick={() => setShowCertificationModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">Жаңа сертификат</div>
              <button
                className="btn btn-outline-secondary"
                onClick={() => setShowCertificationModal(false)}
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleCertificationSubmit}>
              <div className="mb-4">
                <label className="label">Сертификат атауы *</label>
                <input
                  type="text"
                  className="input"
                  value={certificationForm.certification_name}
                  onChange={(e) => setCertificationForm({ ...certificationForm, certification_name: e.target.value })}
                  required
                />
              </div>
              <div className="mb-4">
                <label className="label">Берген ұйым *</label>
                <input
                  type="text"
                  className="input"
                  value={certificationForm.issuing_organization}
                  onChange={(e) => setCertificationForm({ ...certificationForm, issuing_organization: e.target.value })}
                  required
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="label">Сертификат нөмірі</label>
                  <input
                    type="text"
                    className="input"
                    value={certificationForm.certificate_number}
                    onChange={(e) => setCertificationForm({ ...certificationForm, certificate_number: e.target.value })}
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="label">Берілген күні</label>
                  <input
                    type="date"
                    className="input"
                    value={certificationForm.issue_date}
                    onChange={(e) => setCertificationForm({ ...certificationForm, issue_date: e.target.value })}
                  />
                </div>
                <div>
                  <label className="label">Аяқталған күні</label>
                  <input
                    type="date"
                    className="input"
                    value={certificationForm.expiry_date}
                    onChange={(e) => setCertificationForm({ ...certificationForm, expiry_date: e.target.value })}
                  />
                </div>
              </div>
              <div className="mb-4">
                <label className="label">Құжат сілтемесі</label>
                <input
                  type="text"
                  className="input"
                  value={certificationForm.document_url}
                  onChange={(e) => setCertificationForm({ ...certificationForm, document_url: e.target.value })}
                />
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowCertificationModal(false)}
                >
                  Жабу
                </button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? "Жүктелуде..." : "Сақтау"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

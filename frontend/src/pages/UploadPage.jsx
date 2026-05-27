import { useState } from "react";
import api from "../api/api";

const sourceOptions = [
    {
        value: "sap",
        label: "SAP",
        scope: "Scope 1",
        detail: "Fuel and procurement exports",
    },
    {
        value: "utility",
        label: "Utility",
        scope: "Scope 2",
        detail: "Electricity usage exports",
    },
    {
        value: "travel",
        label: "Travel",
        scope: "Scope 3",
        detail: "Flights and business travel",
    },
];

function UploadPage() {

    const [sourceType, setSourceType] = useState("sap");

    const [file, setFile] = useState(null);

    const [loading, setLoading] = useState(false);

    const [response, setResponse] = useState(null);

    const [error, setError] = useState("");

    const selectedSource = sourceOptions.find((source) => source.value === sourceType);

    const handleUpload = async (e) => {

        e.preventDefault();

        setError("");
        setResponse(null);

        if (!file) {
            setError("Please select a file before uploading.");
            return;
        }

        const formData = new FormData();

        formData.append("source_type", sourceType);

        formData.append("file", file);

        try {

            setLoading(true);

            const res = await api.post(
                "/ingest/upload/",
                formData,
                {
                    headers: {
                        "Content-Type": "multipart/form-data",
                    },
                }
            );

            setResponse(res.data);

        } catch (err) {

            console.error(err);

            const errorMessage =
                err.response?.data?.error ||
                err.response?.data?.detail ||
                err.message ||
                "Upload failed";

            setError(`Upload failed: ${errorMessage}`);

        } finally {

            setLoading(false);
        }
    };

    return (

        <div className="app-shell">

            <header className="topbar">
                <div>
                    <p className="eyebrow">Breathe ESG prototype</p>
                    <h1>Smart Ingestion Engine</h1>
                </div>
                <a
                    className="api-link"
                    href="https://smart-ingestion-engine.onrender.com/api/ingest/upload/"
                    target="_blank"
                    rel="noreferrer"
                >
                    API
                </a>
            </header>

            <main className="workspace">
                <section className="upload-panel">
                    <div className="panel-heading">
                        <div>
                            <p className="eyebrow">New ingestion batch</p>
                            <h2>Upload source data</h2>
                        </div>
                        <span className="status-pill">PostgreSQL live</span>
                    </div>

                    <form onSubmit={handleUpload} className="upload-form">
                        <div className="field-block">
                            <label>Source type</label>
                            <div className="source-grid">
                                {sourceOptions.map((source) => (
                                    <button
                                        className={`source-card ${sourceType === source.value ? "active" : ""}`}
                                        key={source.value}
                                        type="button"
                                        onClick={() => setSourceType(source.value)}
                                    >
                                        <span>{source.label}</span>
                                        <strong>{source.scope}</strong>
                                        <small>{source.detail}</small>
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="field-block">
                            <label htmlFor="source-file">Source file</label>
                            <label className="file-drop" htmlFor="source-file">
                                <input
                                    id="source-file"
                                    type="file"
                                    accept=".csv,.tsv,.txt"
                                    onChange={(e) => setFile(e.target.files[0])}
                                />
                                <span className="file-icon">CSV</span>
                                <span>
                                    <strong>{file ? file.name : "Choose a source export"}</strong>
                                    <small>{file ? `${Math.max(1, Math.round(file.size / 1024))} KB selected` : `${selectedSource.label} ${selectedSource.scope} upload`}</small>
                                </span>
                            </label>
                        </div>

                        {error && <div className="alert error">{error}</div>}

                        <button className="primary-button" type="submit" disabled={loading}>
                            {loading ? "Uploading..." : "Upload batch"}
                        </button>
                    </form>
                </section>

                <aside className="result-panel">
                    <div className="panel-heading">
                        <div>
                            <p className="eyebrow">Batch output</p>
                            <h2>Upload result</h2>
                        </div>
                    </div>

                    {!response && !loading && (
                        <div className="empty-state">
                            <span>Ready</span>
                            <p>Select a source export to create an ingestion batch.</p>
                        </div>
                    )}

                    {loading && (
                        <div className="empty-state">
                            <span>Processing</span>
                            <p>Parsing rows and writing normalized records.</p>
                        </div>
                    )}

                    {response && (
                        <div className="result-stack">
                            <div className="success-banner">{response.message}</div>
                            <div className="metric-grid">
                                <div>
                                    <span>Records</span>
                                    <strong>{response.records_created}</strong>
                                </div>
                                <div>
                                    <span>Parse errors</span>
                                    <strong>{response.parse_errors}</strong>
                                </div>
                            </div>
                            <div className="batch-id">
                                <span>Batch ID</span>
                                <code>{response.batch_id}</code>
                            </div>
                            <pre>{JSON.stringify(response, null, 2)}</pre>
                        </div>
                    )}
                </aside>
            </main>

        </div>
    );
}

export default UploadPage;

import { useState } from "react";
import api from "../api/api";

function UploadPage() {

    const [sourceType, setSourceType] = useState("sap");

    const [file, setFile] = useState(null);

    const [loading, setLoading] = useState(false);

    const [response, setResponse] = useState(null);

    const handleUpload = async (e) => {

        e.preventDefault();

        if (!file) {
            alert("Please select a file");
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

            alert("Upload failed");

        } finally {

            setLoading(false);
        }
    };

    return (

        <div style={{ padding: "40px" }}>

            <h1>
                Upload ESG Data
            </h1>

            <form onSubmit={handleUpload}>

                <div style={{ marginBottom: "20px" }}>

                    <label>
                        Source Type
                    </label>

                    <br />

                    <select
                        value={sourceType}
                        onChange={(e) => setSourceType(e.target.value)}
                    >

                        <option value="sap">
                            SAP
                        </option>

                        <option value="utility">
                            Utility
                        </option>

                        <option value="travel">
                            Travel
                        </option>

                    </select>

                </div>

                <div style={{ marginBottom: "20px" }}>

                    <input
                        type="file"
                        onChange={(e) => setFile(e.target.files[0])}
                    />

                </div>

                <button type="submit">

                    {loading ? "Uploading..." : "Upload"}

                </button>

            </form>

            {response && (

                <div style={{ marginTop: "30px" }}>

                    <h3>
                        Upload Result
                    </h3>

                    <pre>
                        {JSON.stringify(response, null, 2)}
                    </pre>

                </div>
            )}

        </div>
    );
}

export default UploadPage;
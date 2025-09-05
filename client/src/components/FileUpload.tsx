import React, { useState, useEffect } from "react";
import { Upload, FileText } from "lucide-react";
import { useAppContext } from "../context/AppContext";

const FileUpload: React.FC = () => {
    const { state, loadCompanies } = useAppContext();
    const [files, setFiles] = useState<File[]>([]);
    const [message, setMessage] = useState("");
    const [isUploading, setIsUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [progressStatus, setProgressStatus] = useState("");

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setFiles(Array.from(e.target.files));
            setMessage("");
        }
    };

    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        if (e.dataTransfer.files) {
            setFiles(Array.from(e.dataTransfer.files));
            setMessage("");
        }
    };

    const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
    };

    const handleUpload = async () => {
        if (files.length === 0) {
            setMessage("Please select a file first!");
            return;
        }

        setIsUploading(true);
        setProgress(0);
        setProgressStatus("Uploading file...");

        try {
            const formData = new FormData();
            formData.append('file', files[0]);

            const response = await fetch('http://localhost:5000/api/upload', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok || response.status === 202) {
                // Start listening to Server-Sent Events for real progress
                if (result.session_id) {
                    console.log("Starting SSE connection for session:", result.session_id);
                    
                    const eventSource = new EventSource(`http://localhost:5000/api/progress/${result.session_id}`);
                    
                    eventSource.onopen = () => {
                        console.log("SSE connection opened");
                        setProgress(5);
                        setProgressStatus("Connected to progress tracking...");
                    };
                    
                    eventSource.onmessage = (event) => {
                        try {
                            console.log("Received SSE data:", event.data);
                            const data = JSON.parse(event.data);
                            setProgress(data.progress);
                            setProgressStatus(data.status);
                            
                            // When processing is complete
                            if (data.completed) {
                                console.log("Processing completed");
                                eventSource.close();
                                setMessage("✅ File uploaded and processed successfully");
                                setFiles([]);
                                
                                // Reload companies
                                loadCompanies();
                                
                                // Clean up after 2 seconds
                                setTimeout(() => {
                                    setIsUploading(false);
                                    setProgress(0);
                                    setProgressStatus("");
                                }, 2000);
                            }
                        } catch (error) {
                            console.error("Error parsing progress data:", error);
                            eventSource.close();
                            setIsUploading(false);
                            setMessage("❌ Error parsing progress data");
                        }
                    };
                    
                    eventSource.onerror = (error) => {
                        console.error("SSE Error:", error);
                        console.error("EventSource readyState:", eventSource.readyState);
                        eventSource.close();
                        
                        // Fallback to simple completion check
                        setProgressStatus("Progress tracking failed, checking completion...");
                        const checkInterval = setInterval(async () => {
                            try {
                                const companiesResponse = await fetch('http://localhost:5000/api/companies');
                                const companiesData = await companiesResponse.json();
                                
                                if (companiesData.companies && companiesData.companies.length > 0) {
                                    clearInterval(checkInterval);
                                    setProgress(100);
                                    setProgressStatus("Processing completed!");
                                    setMessage("✅ File processed successfully (progress tracking failed)");
                                    loadCompanies();
                                    
                                    setTimeout(() => {
                                        setIsUploading(false);
                                        setProgress(0);
                                        setProgressStatus("");
                                    }, 2000);
                                }
                            } catch (e) {
                                console.error("Error checking completion:", e);
                            }
                        }, 3000);
                        
                        // Timeout after 2 minutes
                        setTimeout(() => {
                            clearInterval(checkInterval);
                            setIsUploading(false);
                            setMessage("❌ Processing timeout - please check if file was processed");
                        }, 120000);
                    };
                } else {
                    // Fallback if no session ID
                    setMessage("✅ Upload started but progress tracking unavailable");
                    setIsUploading(false);
                }
            } else {
                setMessage(`❌ ${result.error || "Upload failed"}`);
                setIsUploading(false);
                setProgress(0);
                setProgressStatus("");
            }
        } catch (error) {
            console.error("Upload error:", error);
            setMessage(`❌ Error uploading file: ${error instanceof Error ? error.message : 'Unknown error'}`);
            setIsUploading(false);
            setProgress(0);
            setProgressStatus("");
        }
    };

    return (
        <div className="mb-8">
            <h2 className="text-lg font-semibold mb-3">Upload Financial Reports 📂</h2>

            {/* Show processing indicator if backend is busy */}
            {state.isLoading && (
                <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                    <div className="flex items-center gap-3">
                        <div className="animate-spin w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                        <span className="text-blue-700 dark:text-blue-300">
                            Processing PDF in background... This may take a few minutes for large files.
                        </span>
                    </div>
                </div>
            )}

            {/* TEST PROGRESS BAR - Always visible for testing */}
            <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="text-sm font-medium text-yellow-800 mb-2">
                    Test Progress Bar - Upload State: {isUploading ? "UPLOADING" : "NOT UPLOADING"}
                </div>
                <div className="w-full bg-yellow-200 rounded-full h-3">
                    <div
                        className="h-3 bg-yellow-600 rounded-full transition-all duration-300"
                        style={{ width: `${progress}%` }}
                    />
                </div>
                <div className="text-xs text-yellow-700 mt-1">
                    Progress: {Math.round(progress)}% | Status: {progressStatus || "Ready"}
                </div>
            </div>

            {/* Upload Box */}
            <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                className="flex items-center justify-between bg-gray-200 dark:bg-gray-800 p-6 rounded-lg border border-dashed border-gray-400 dark:border-gray-600 cursor-pointer"
            >
                <div className="flex items-center gap-3">
                    <Upload className="w-6 h-6 text-gray-500 dark:text-gray-300" />
                    <span className="text-gray-700 dark:text-gray-300">
                        Drag and drop files here <br />
                        <span className="text-sm text-gray-500">
                            Limit 200MB per file • PDF
                        </span>
                    </span>
                </div>

                <label className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 cursor-pointer">
                    Browse files
                    <input
                        type="file"
                        accept="application/pdf"
                        onChange={handleFileChange}
                        className="hidden"
                    />
                </label>
            </div>

            {/* Upload Button */}
            {files.length > 0 && (
                <div className="mt-4 flex flex-col gap-2">
                    <ul className="space-y-1">
                        {files.map((file, index) => (
                            <li
                                key={index}
                                className="flex items-center gap-2 text-sm text-gray-800 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 px-3 py-2 rounded"
                            >
                                <FileText className="w-4 h-4 text-blue-500" />
                                {file.name}{" "}
                                <span className="ml-auto text-xs text-gray-500">
                                    {(file.size / 1024 / 1024).toFixed(2)} MB
                                </span>
                            </li>
                        ))}
                    </ul>

                    <button
                        onClick={handleUpload}
                        disabled={state.isLoading || isUploading}
                        className={`px-4 py-2 rounded text-white ${
                            state.isLoading || isUploading 
                                ? "bg-gray-400" 
                                : "bg-green-600 hover:bg-green-700"
                        }`}
                    >
                        {isUploading ? "Processing..." : "Upload"}
                    </button>

                    {/* Simple Progress Bar */}
                    {isUploading && (
                        <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                            <div className="flex justify-between items-center mb-2">
                                <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                                    {progressStatus}
                                </span>
                                <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                                    {Math.round(progress)}%
                                </span>
                            </div>
                            
                            <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-3">
                                <div
                                    className="h-3 bg-blue-600 rounded-full transition-all duration-300 ease-out"
                                    style={{ width: `${progress}%` }}
                                />
                            </div>
                        </div>
                    )}

                    {state.error && (
                        <p className="text-sm mt-2 text-red-600 dark:text-red-400">
                            {state.error}
                        </p>
                    )}

                    {message && !state.error && (
                        <p className="text-sm mt-2 text-gray-700 dark:text-gray-300">
                            {message}
                        </p>
                    )}
                </div>
            )}
        </div>
    );
};

export default FileUpload;

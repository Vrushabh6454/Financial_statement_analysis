import React, { useState } from "react";
import { Upload, FileText } from "lucide-react";
import { useAppContext } from "../context/AppContext";

const FileUpload: React.FC = () => {
    const { state, uploadFile } = useAppContext();
    const [files, setFiles] = useState<File[]>([]);
    const [message, setMessage] = useState("");

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

        try {
            await uploadFile(files[0]);
            setMessage(`✅ File uploaded and processed successfully`);
            setFiles([]);
        } catch (error) {
            let errorMessage = "Error uploading file.";
            if (error instanceof Error) {
                errorMessage = error.message;
            }
            setMessage(`❌ ${errorMessage}`);
        }
    };

    return (
        <div className="mb-8">
            <h2 className="text-lg font-semibold mb-3">Upload Financial Reports 📂</h2>

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
                        disabled={state.isLoading}
                        className={`px-4 py-2 rounded text-white ${state.isLoading ? "bg-gray-400" : "bg-green-600 hover:bg-green-700"
                            }`}
                    >
                        {state.isLoading ? "Processing..." : "Upload"}
                    </button>

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

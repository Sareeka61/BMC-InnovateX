import React from "react";
import PropTypes from "prop-types";

const VideoUploader = ({
  onVideoUpload,
  onResetCounts,
  className = "",
  isDarkMode,
}) => {
  const handleVideoUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith("video/")) {
      alert("Please upload a valid video file");
      return;
    }

    // Validate file size (max 100MB)
    if (file.size > 100 * 1024 * 1024) {
      alert("File size should be less than 100MB");
      return;
    }

    const videoUrl = URL.createObjectURL(file);

    // Reset counts when new video is uploaded
    onResetCounts();

    // Pass the video URL to parent component
    onVideoUpload(videoUrl);
  };

  return (
    <div className={`mb-4 ${className}`}>
      <input
        type="file"
        accept="video/*"
        onChange={handleVideoUpload}
        className={`block w-full text-sm ${
          isDarkMode
            ? "text-slate-300 file:bg-slate-700 file:text-white file:border-slate-600 file:hover:bg-slate-600"
            : "text-gray-500 file:bg-blue-50 file:text-blue-700 file:hover:bg-blue-100"
        }
          file:mr-4 file:py-2 file:px-4
          file:rounded-full file:border-0
          file:text-sm file:font-semibold
          focus:outline-none focus:ring-2 focus:ring-blue-500
          transition-all duration-200`}
        aria-label="Upload video file"
      />
      <p
        className={`mt-2 text-xs ${
          isDarkMode ? "text-slate-400" : "text-gray-500"
        }`}
      >
        Supported formats: MP4, WebM, Ogg (Max size: 100MB)
      </p>
    </div>
  );
};

VideoUploader.propTypes = {
  onVideoUpload: PropTypes.func.isRequired,
  onResetCounts: PropTypes.func.isRequired,
  className: PropTypes.string,
  isDarkMode: PropTypes.bool,
};

export default VideoUploader;

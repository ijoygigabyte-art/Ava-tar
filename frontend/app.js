const API_URL = 'http://127.0.0.1:8000/api/v1/videos';

// DOM Elements
const uploadForm = document.getElementById('uploadForm');
const videoTitle = document.getElementById('videoTitle');
const videoFile = document.getElementById('videoFile');
const fileDropArea = document.getElementById('fileDropArea');
const fileDetail = document.getElementById('fileDetail');
const uploadBtn = document.getElementById('uploadBtn');
const uploadStatus = document.getElementById('uploadStatus');
const btnText = document.querySelector('.btn-text');
const loader = document.querySelector('.loader');
const videoList = document.getElementById('videoList');
const refreshBtn = document.getElementById('refreshBtn');

// Video Player Modal Elements
const videoModal = document.getElementById('videoModal');
const closeModalBtn = document.getElementById('closeModalBtn');
const hlsPlayer = document.getElementById('hlsPlayer');
const modalVideoTitle = document.getElementById('modalVideoTitle');
let hlsInstance = null;

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    fetchVideos();
    setupDragAndDrop();
});

// Drag and drop setup
function setupDragAndDrop() {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, () => fileDropArea.classList.add('drag-over'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, () => fileDropArea.classList.remove('drag-over'), false);
    });

    fileDropArea.addEventListener('drop', handleDrop, false);
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (files.length > 0) {
        videoFile.files = files; // Assign files to input
        updateFileDetail(files[0]);
    }
}

videoFile.addEventListener('change', function () {
    if (this.files.length > 0) {
        updateFileDetail(this.files[0]);
    }
});

function updateFileDetail(file) {
    const size = (file.size / (1024 * 1024)).toFixed(2); // Convert to MB
    fileDetail.innerHTML = `
        <span>🎥 ${file.name}</span>
        <span>${size} MB</span>
    `;
    fileDetail.classList.remove('hidden');
}

// Set UI state for loading
function setLoading(isLoading) {
    uploadBtn.disabled = isLoading;
    videoTitle.disabled = isLoading;
    videoFile.disabled = isLoading;

    if (isLoading) {
        btnText.classList.add('hidden');
        loader.classList.remove('hidden');
    } else {
        btnText.classList.remove('hidden');
        loader.classList.add('hidden');
    }
}

// Display messages
function showMessage(msg, type) {
    uploadStatus.textContent = msg;
    uploadStatus.className = `status-msg ${type}`;

    if (type === 'success') {
        setTimeout(() => {
            uploadStatus.textContent = '';
            uploadStatus.className = 'status-msg';
        }, 5000);
    }
}

// Upload Form Handler
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const title = videoTitle.value.trim();
    const file = videoFile.files[0];

    if (!title || !file) {
        showMessage("Please provide a title and select a video file.", "error");
        return;
    }

    setLoading(true);
    showMessage("Initializing upload...", "");

    try {
        // Step 1: Upload file directly to Backend using FormData
        const formData = new FormData();
        formData.append('title', title);
        formData.append('file', file);

        const uploadRes = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!uploadRes.ok) {
            const errorText = await uploadRes.text();
            console.error("Upload failed with status:", uploadRes.status);
            console.error("Error response:", errorText);
            throw new Error(`Failed to upload video to backend (Status: ${uploadRes.status}).`);
        }

        const data = await uploadRes.json();

        // Success Cleanup
        showMessage("Upload complete! Video is now processing.", "success");
        uploadForm.reset();
        fileDetail.classList.add('hidden');
        fetchVideos(); // Refresh the list

    } catch (err) {
        console.error(err);
        showMessage(err.message || "An unexpected error occurred during upload.", "error");
    } finally {
        setLoading(false);
    }
});

// Refresh Button
refreshBtn.addEventListener('click', () => {
    fetchVideos();
    const icon = refreshBtn.querySelector('svg');
    icon.style.transform = 'rotate(180deg)';
    icon.style.transition = 'transform 0.4s ease';
    setTimeout(() => icon.style.transform = '', 400);
});

// Fetch videos to build gallery
async function fetchVideos() {
    try {
        const res = await fetch(API_URL);
        if (!res.ok) throw new Error("Could not fetch videos");

        const videos = await res.json();
        renderGallery(videos);
    } catch (err) {
        console.error("Gallery Error:", err);
        videoList.innerHTML = `<p class="status-msg error">Failed to load videos. Is backend running?</p>`;
    }
}

// Render Gallery
function renderGallery(videos) {
    if (!videos || videos.length === 0) {
        videoList.innerHTML = `<p style="color:var(--text-secondary);grid-column:1/-1;text-align:center;padding:2rem 0;">No videos uploaded yet. Add one to see it here!</p>`;
        return;
    }

    // Sort newest first
    videos.sort((a, b) => b.id - a.id);

    videoList.innerHTML = videos.map(v => {
        let statusClass = "pending";
        let statusText = "Pending";
        let playDisabled = "disabled";

        if (v.status === 'processing') {
            statusClass = 'processing'; statusText = 'Processing...';
        } else if (v.status === 'completed') {
            statusClass = 'completed'; statusText = 'Ready';
            playDisabled = "";
        } else if (v.status === 'failed') {
            statusClass = 'failed'; statusText = 'Failed';
        }

        return `
        <div class="video-card">
            <div class="video-thumbnail-placeholder">
                <svg class="video-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect>
                    <line x1="7" y1="2" x2="7" y2="22"></line>
                    <line x1="17" y1="2" x2="17" y2="22"></line>
                    <line x1="2" y1="12" x2="22" y2="12"></line>
                    <line x1="2" y1="7" x2="7" y2="7"></line>
                    <line x1="2" y1="17" x2="7" y2="17"></line>
                    <line x1="17" y1="17" x2="22" y2="17"></line>
                    <line x1="17" y1="7" x2="22" y2="7"></line>
                </svg>
            </div>
            <div class="video-info">
                <span class="video-title" title="${v.title}">${v.title}</span>
                <span class="status-badge ${statusClass}">${statusText}</span>
            </div>
            <button class="play-action-btn" onclick="openPlayer('${v.hls_url}', '${v.title.replace(/'/g, "\\'")}')" ${playDisabled}>
                ${v.status === 'completed' ? '▶ Play Video' : 'Not Ready'}
            </button>
        </div>
        `;
    }).join("");
}

// Video Player Modal Logic
function openPlayer(hlsUrl, title) {
    if (!hlsUrl || hlsUrl === "null") {
        alert("Video stream is not available yet.");
        return;
    }

    modalVideoTitle.textContent = title;
    videoModal.classList.remove('hidden');

    if (Hls.isSupported()) {
        if (hlsInstance) { hlsInstance.destroy(); }

        hlsInstance = new Hls();
        hlsInstance.loadSource(hlsUrl);
        hlsInstance.attachMedia(hlsPlayer);
        hlsInstance.on(Hls.Events.MANIFEST_PARSED, function () {
            hlsPlayer.play();
        });
    } else if (hlsPlayer.canPlayType('application/vnd.apple.mpegurl')) {
        // For Safari support which has native HLS natively
        hlsPlayer.src = hlsUrl;
        hlsPlayer.addEventListener('loadedmetadata', function () {
            hlsPlayer.play();
        });
    }
}

function closePlayer() {
    videoModal.classList.add('hidden');
    hlsPlayer.pause();
    if (hlsInstance) {
        hlsInstance.destroy();
        hlsInstance = null;
    }
}

closeModalBtn.addEventListener('click', closePlayer);

// Close modal if clicking outside the content
videoModal.addEventListener('click', (e) => {
    if (e.target === videoModal) {
        closePlayer();
    }
});

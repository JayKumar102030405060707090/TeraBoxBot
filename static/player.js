// TeraBox Bot Player JavaScript

// Global variables
let currentVideo = null;
let isFullscreen = false;
let videoStats = {
    totalVideos: 0,
    totalStreams: 0,
    totalDownloads: 0
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializePlayer();
    loadStatistics();
    setupEventListeners();
    checkMobileDevice();
});

// Initialize video player
function initializePlayer() {
    const video = document.getElementById('mainVideoPlayer');
    if (!video) return;
    
    currentVideo = video;
    
    // Video event listeners
    video.addEventListener('loadstart', handleVideoLoadStart);
    video.addEventListener('canplay', handleVideoCanPlay);
    video.addEventListener('error', handleVideoError);
    video.addEventListener('loadedmetadata', handleVideoMetadata);
    video.addEventListener('play', handleVideoPlay);
    video.addEventListener('pause', handleVideoPause);
    video.addEventListener('ended', handleVideoEnded);
    video.addEventListener('timeupdate', handleVideoTimeUpdate);
    video.addEventListener('volumechange', handleVideoVolumeChange);
    
    // Custom controls
    setupCustomControls();
    
    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
}

// Video event handlers
function handleVideoLoadStart() {
    showLoadingOverlay(true);
    console.log('Video loading started');
}

function handleVideoCanPlay() {
    showLoadingOverlay(false);
    console.log('Video can play');
}

function handleVideoError(e) {
    showLoadingOverlay(false);
    console.error('Video error:', e);
    
    const video = e.target;
    const errorCode = video.error ? video.error.code : 'unknown';
    
    // Try alternative source
    tryAlternativeSource(video);
    
    // Show error notification
    showNotification('Video loading failed. Trying alternative source...', 'warning');
}

function handleVideoMetadata() {
    const video = currentVideo;
    if (!video) return;
    
    updateVideoDuration(video.duration);
    updateVideoQuality(video.videoWidth, video.videoHeight);
    
    console.log(`Video metadata loaded: ${video.videoWidth}x${video.videoHeight}, ${video.duration}s`);
}

function handleVideoPlay() {
    updatePlayButton(true);
    trackVideoEvent('play');
}

function handleVideoPause() {
    updatePlayButton(false);
    trackVideoEvent('pause');
}

function handleVideoEnded() {
    updatePlayButton(false);
    trackVideoEvent('ended');
    showNotification('Video playback completed', 'success');
}

function handleVideoTimeUpdate() {
    updateProgressBar();
}

function handleVideoVolumeChange() {
    updateVolumeDisplay();
}

// Custom controls setup
function setupCustomControls() {
    // Add fullscreen button functionality
    const fullscreenBtn = document.querySelector('.fullscreen-btn');
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', toggleFullscreen);
    }
    
    // Add quality selector
    createQualitySelector();
    
    // Add speed controls
    createSpeedControls();
}

// Keyboard shortcuts
function handleKeyboardShortcuts(e) {
    if (!currentVideo) return;
    
    // Don't handle shortcuts if user is typing
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    
    switch(e.code) {
        case 'Space':
            e.preventDefault();
            togglePlayPause();
            break;
        case 'ArrowLeft':
            e.preventDefault();
            seekVideo(-10);
            break;
        case 'ArrowRight':
            e.preventDefault();
            seekVideo(10);
            break;
        case 'ArrowUp':
            e.preventDefault();
            adjustVolume(0.1);
            break;
        case 'ArrowDown':
            e.preventDefault();
            adjustVolume(-0.1);
            break;
        case 'KeyF':
            e.preventDefault();
            toggleFullscreen();
            break;
        case 'KeyM':
            e.preventDefault();
            toggleMute();
            break;
    }
}

// Player control functions
function togglePlayPause() {
    if (!currentVideo) return;
    
    if (currentVideo.paused) {
        currentVideo.play();
    } else {
        currentVideo.pause();
    }
}

function seekVideo(seconds) {
    if (!currentVideo) return;
    
    currentVideo.currentTime = Math.max(0, Math.min(currentVideo.duration, currentVideo.currentTime + seconds));
}

function adjustVolume(delta) {
    if (!currentVideo) return;
    
    currentVideo.volume = Math.max(0, Math.min(1, currentVideo.volume + delta));
}

function toggleMute() {
    if (!currentVideo) return;
    
    currentVideo.muted = !currentVideo.muted;
}

function toggleFullscreen() {
    if (!currentVideo) return;
    
    const container = currentVideo.closest('.video-container');
    
    if (!isFullscreen) {
        if (container.requestFullscreen) {
            container.requestFullscreen();
        } else if (container.webkitRequestFullscreen) {
            container.webkitRequestFullscreen();
        } else if (container.msRequestFullscreen) {
            container.msRequestFullscreen();
        }
        isFullscreen = true;
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
        isFullscreen = false;
    }
}

// UI update functions
function updatePlayButton(isPlaying) {
    const playBtn = document.querySelector('.play-btn i');
    if (playBtn) {
        playBtn.className = isPlaying ? 'fas fa-pause' : 'fas fa-play';
    }
}

function updateProgressBar() {
    if (!currentVideo) return;
    
    const progress = (currentVideo.currentTime / currentVideo.duration) * 100;
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
    }
    
    // Update time display
    const currentTimeEl = document.querySelector('.current-time');
    const durationEl = document.querySelector('.duration');
    
    if (currentTimeEl) {
        currentTimeEl.textContent = formatTime(currentVideo.currentTime);
    }
    if (durationEl) {
        durationEl.textContent = formatTime(currentVideo.duration);
    }
}

function updateVolumeDisplay() {
    if (!currentVideo) return;
    
    const volumeBar = document.querySelector('.volume-bar');
    if (volumeBar) {
        volumeBar.style.width = `${currentVideo.volume * 100}%`;
    }
    
    const muteBtn = document.querySelector('.mute-btn i');
    if (muteBtn) {
        muteBtn.className = currentVideo.muted || currentVideo.volume === 0 
            ? 'fas fa-volume-mute' 
            : 'fas fa-volume-up';
    }
}

function updateVideoDuration(duration) {
    const durationElement = document.getElementById('videoDuration');
    if (durationElement && duration) {
        durationElement.textContent = formatTime(duration);
    }
}

function updateVideoQuality(width, height) {
    const qualityElement = document.querySelector('.video-quality');
    if (qualityElement) {
        const quality = getVideoQuality(width, height);
        qualityElement.textContent = quality;
    }
}

// Alternative source handling
function tryAlternativeSource(video) {
    const currentSrc = video.currentSrc;
    
    // If already using proxy, try direct link
    if (currentSrc.includes('/proxy/')) {
        const videoId = window.location.pathname.split('/').pop();
        fetch(`/api/video/${videoId}`)
            .then(response => response.json())
            .then(data => {
                if (data.video_url && data.video_url !== currentSrc) {
                    video.src = data.video_url;
                    video.load();
                    showNotification('Trying direct video link...', 'info');
                }
            });
    } else {
        // Try proxy
        const videoId = window.location.pathname.split('/').pop();
        const proxyUrl = `/proxy/${videoId}`;
        video.src = proxyUrl;
        video.load();
        showNotification('Trying alternative server...', 'info');
    }
}

// Quality selector
function createQualitySelector() {
    const videoId = window.location.pathname.split('/').pop();
    if (!videoId) return;
    
    fetch(`/api/video/${videoId}`)
        .then(response => response.json())
        .then(data => {
            if (data.download_urls && data.download_urls.length > 1) {
                const qualitySelector = document.createElement('select');
                qualitySelector.className = 'form-select form-select-sm bg-dark text-light';
                qualitySelector.innerHTML = '<option>Auto Quality</option>';
                
                data.download_urls.forEach((url, index) => {
                    const option = document.createElement('option');
                    option.value = url;
                    option.textContent = `Quality ${index + 1}`;
                    qualitySelector.appendChild(option);
                });
                
                qualitySelector.addEventListener('change', function() {
                    if (this.value && currentVideo) {
                        const currentTime = currentVideo.currentTime;
                        currentVideo.src = this.value;
                        currentVideo.load();
                        currentVideo.currentTime = currentTime;
                    }
                });
                
                const controlsContainer = document.querySelector('.video-controls');
                if (controlsContainer) {
                    controlsContainer.appendChild(qualitySelector);
                }
            }
        });
}

// Speed controls
function createSpeedControls() {
    const speeds = [0.5, 0.75, 1, 1.25, 1.5, 2];
    const speedSelector = document.createElement('select');
    speedSelector.className = 'form-select form-select-sm bg-dark text-light';
    
    speeds.forEach(speed => {
        const option = document.createElement('option');
        option.value = speed;
        option.textContent = `${speed}x`;
        option.selected = speed === 1;
        speedSelector.appendChild(option);
    });
    
    speedSelector.addEventListener('change', function() {
        if (currentVideo) {
            currentVideo.playbackRate = parseFloat(this.value);
        }
    });
    
    const controlsContainer = document.querySelector('.video-controls');
    if (controlsContainer) {
        controlsContainer.appendChild(speedSelector);
    }
}

// Loading overlay
function showLoadingOverlay(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = show ? 'flex' : 'none';
    }
}

// Statistics
function loadStatistics() {
    fetch('/stats')
        .then(response => response.json())
        .then(data => {
            videoStats = data;
            updateStatsDisplay();
        })
        .catch(error => {
            console.error('Error loading statistics:', error);
        });
}

function updateStatsDisplay() {
    const elements = {
        totalVideos: document.getElementById('totalVideos'),
        totalStreams: document.getElementById('totalStreams'),
        totalDownloads: document.getElementById('totalDownloads')
    };
    
    Object.keys(elements).forEach(key => {
        if (elements[key]) {
            animateNumber(elements[key], videoStats[key] || 0);
        }
    });
}

function animateNumber(element, target) {
    const start = parseInt(element.textContent) || 0;
    const duration = 1000;
    const stepTime = 50;
    const steps = duration / stepTime;
    const increment = (target - start) / steps;
    
    let current = start;
    const timer = setInterval(() => {
        current += increment;
        element.textContent = Math.round(current);
        
        if (Math.abs(current - target) < 1) {
            element.textContent = target;
            clearInterval(timer);
        }
    }, stepTime);
}

// Event listeners setup
function setupEventListeners() {
    // Share button
    const shareBtn = document.querySelector('.share-btn');
    if (shareBtn) {
        shareBtn.addEventListener('click', shareVideo);
    }
    
    // Download buttons
    document.querySelectorAll('.download-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            trackVideoEvent('download_click');
        });
    });
    
    // Fullscreen change events
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('msfullscreenchange', handleFullscreenChange);
}

function handleFullscreenChange() {
    isFullscreen = !!(document.fullscreenElement || document.webkitFullscreenElement || document.msFullscreenElement);
    
    const fullscreenBtn = document.querySelector('.fullscreen-btn i');
    if (fullscreenBtn) {
        fullscreenBtn.className = isFullscreen ? 'fas fa-compress' : 'fas fa-expand';
    }
}

// Mobile device detection and optimization
function checkMobileDevice() {
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isMobile) {
        document.body.classList.add('mobile-device');
        
        // Add mobile-specific optimizations
        if (currentVideo) {
            currentVideo.setAttribute('playsinline', '');
            currentVideo.setAttribute('webkit-playsinline', '');
        }
        
        // Show mobile tips
        showMobileTips();
    }
}

function showMobileTips() {
    const tipContainer = document.createElement('div');
    tipContainer.className = 'alert alert-info mobile-tip';
    tipContainer.innerHTML = `
        <i class="fas fa-mobile-alt me-2"></i>
        <strong>Mobile Tip:</strong> Rotate your device for better viewing experience.
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(tipContainer, container.firstChild);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            tipContainer.remove();
        }, 5000);
    }
}

// Utility functions
function formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return '0:00';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}

function getVideoQuality(width, height) {
    if (height >= 2160) return '4K';
    if (height >= 1440) return '1440p';
    if (height >= 1080) return '1080p';
    if (height >= 720) return '720p';
    if (height >= 480) return '480p';
    if (height >= 360) return '360p';
    return '240p';
}

function trackVideoEvent(event) {
    // Analytics tracking
    console.log(`Video event: ${event}`);
    
    // You can add actual analytics tracking here
    if (typeof gtag !== 'undefined') {
        gtag('event', event, {
            event_category: 'video',
            event_label: window.location.pathname
        });
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification fade-in`;
    notification.innerHTML = `
        <i class="fas fa-${getIconForType(type)} me-2"></i>
        ${message}
    `;
    
    // Position notification
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

function getIconForType(type) {
    const icons = {
        info: 'info-circle',
        success: 'check-circle',
        warning: 'exclamation-triangle',
        danger: 'exclamation-circle'
    };
    return icons[type] || 'info-circle';
}

// Share functionality
function shareVideo() {
    const url = window.location.href;
    const title = document.title;
    
    if (navigator.share) {
        navigator.share({
            title: title,
            url: url,
            text: `Watch this video: ${title}`
        }).then(() => {
            trackVideoEvent('shared');
        }).catch(err => {
            console.log('Error sharing:', err);
            fallbackShare(url, title);
        });
    } else {
        fallbackShare(url, title);
    }
}

function fallbackShare(url, title) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(url).then(() => {
            showNotification('Video URL copied to clipboard!', 'success');
            trackVideoEvent('url_copied');
        }).catch(() => {
            showShareModal(url, title);
        });
    } else {
        showShareModal(url, title);
    }
}

function showShareModal(url, title) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content bg-dark">
                <div class="modal-header">
                    <h5 class="modal-title"><i class="fas fa-share me-2"></i>Share Video</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>Share this video:</p>
                    <div class="input-group">
                        <input type="text" class="form-control" value="${url}" readonly>
                        <button class="btn btn-outline-secondary" onclick="copyToClipboard('${url}')">
                            <i class="fas fa-copy"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    modal.addEventListener('hidden.bs.modal', () => {
        modal.remove();
    });
}

function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copied to clipboard!', 'success');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showNotification('Copied to clipboard!', 'success');
    }
}

// Error handling
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
    showNotification('An error occurred. Please refresh the page.', 'danger');
});

// Performance monitoring
if ('performance' in window) {
    window.addEventListener('load', function() {
        setTimeout(() => {
            const loadTime = performance.now();
            console.log(`Page loaded in ${loadTime.toFixed(2)}ms`);
            
            if (loadTime > 3000) {
                showNotification('Slow connection detected. Video may take longer to load.', 'warning');
            }
        }, 0);
    });
}

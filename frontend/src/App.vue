<template>
  <div class="app-layout">
    <!-- Header with MoMo Branding -->
    <header class="app-header">
      <div class="brand-wrapper">
        <img src="/momo-logo.svg" alt="White Buffalo MoMo Logo" class="brand-logo-img" />
        <div>
          <h1 class="brand-title">
            White Buffalo MoMo
            <span class="brand-suite-tag">Suite · Tool 01</span>
          </h1>
          <p style="font-size: 0.78rem; color: var(--text-muted); margin: 0;">High-Performance Image Compressor</p>
        </div>
      </div>

      <div class="header-meta">
        <div class="status-indicator">
          <span class="status-dot"></span>
          <span>FastAPI Engine Ready</span>
        </div>
      </div>
    </header>

    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-mascot-badge">
        <span>🦬 White Buffalo MoMo · Smart Optimizer</span>
      </div>
      <h2 class="hero-title">
        Compress Images with <br />
        <span class="hero-gradient-text">Zero Visible Quality Loss</span>
      </h2>
      <p class="hero-subtitle">
        TinyPNG-style smart quantization & progressive compression for PNG, JPEG, and WebP. 100% in-memory and stateless.
      </p>
    </section>

    <!-- Settings Bar -->
    <div class="settings-bar">
      <div class="settings-label-group">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3"></circle>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
        </svg>
        <span>Compression Mode:</span>
      </div>

      <div class="settings-presets">
        <button
          class="preset-btn"
          :class="{ active: quality === 90 }"
          @click="setQuality(90)"
        >
          High Quality (90%)
        </button>
        <button
          class="preset-btn"
          :class="{ active: quality === 80 }"
          @click="setQuality(80)"
        >
          Balanced (80%)
        </button>
        <button
          class="preset-btn"
          :class="{ active: quality === 60 }"
          @click="setQuality(60)"
        >
          Max Compression (60%)
        </button>
      </div>

      <div class="slider-container">
        <input
          type="range"
          min="20"
          max="95"
          step="5"
          v-model.number="quality"
          class="quality-slider"
          aria-label="Quality Slider"
        />
        <span class="quality-value">{{ quality }}%</span>
      </div>
    </div>

    <!-- Drag-and-Drop Zone -->
    <div class="dropzone-container">
      <div
        class="dropzone-box"
        :class="{ 'drag-active': isDragging }"
        @dragover.prevent="handleDragOver"
        @dragleave.prevent="handleDragLeave"
        @drop.prevent="handleDrop"
        @click="triggerFileInput"
      >
        <div class="dropzone-content">
          <div class="dropzone-icon-circle">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
          </div>
          <div>
            <h3 class="dropzone-heading">Drop your images here</h3>
            <p class="dropzone-hint">or click to browse from your device</p>
          </div>
          <div class="file-type-chips">
            <span class="chip">PNG</span>
            <span class="chip">JPEG / JPG</span>
            <span class="chip">WEBP</span>
          </div>
        </div>
        <input
          ref="fileInput"
          type="file"
          multiple
          accept="image/png, image/jpeg, image/jpg, image/webp"
          class="file-input-hidden"
          @change="handleFileSelect"
        />
      </div>
    </div>

    <!-- Overall Batch Action Bar -->
    <div v-if="completedCount > 0" class="batch-summary-bar">
      <div class="summary-info">
        <div class="summary-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </div>
        <div>
          <div class="summary-text-main">
            Saved {{ formatBytes(totalSavedBytes) }} total ({{ totalSavingsPercent }}% reduction)
          </div>
          <div class="summary-text-sub">
            {{ completedCount }} of {{ fileQueue.length }} image{{ fileQueue.length > 1 ? 's' : '' }} optimized by MoMo
          </div>
        </div>
      </div>

      <div class="summary-actions">
        <button class="btn-primary" @click="downloadAllAsZip" :disabled="isZipping">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          <span>{{ isZipping ? 'Zipping...' : `Download All (${completedCount})` }}</span>
        </button>
        <button class="btn-secondary" @click="clearAll">
          Clear All
        </button>
      </div>
    </div>

    <!-- Queue List -->
    <div v-if="fileQueue.length > 0" class="queue-list">
      <div v-for="item in fileQueue" :key="item.id" class="queue-item">
        <!-- Thumbnail / Comparison Trigger -->
        <div
          class="item-thumb-wrapper"
          @click="openComparison(item)"
          title="Click to view comparison"
        >
          <img :src="item.dataUrl || item.thumbUrl" :alt="item.name" class="item-thumb" />
        </div>

        <!-- Name & Original Size -->
        <div class="item-info">
          <div class="item-name" :title="item.name">{{ item.name }}</div>
          <div class="item-orig-size">{{ formatBytes(item.originalSizeBytes) }}</div>
        </div>

        <!-- Progress Section -->
        <div class="item-progress-section">
          <div class="progress-track">
            <div
              class="progress-fill"
              :class="{
                loading: item.status === 'compressing',
                success: item.status === 'completed',
                error: item.status === 'error'
              }"
            ></div>
          </div>
          <span class="progress-label" :class="{ 'error-text': item.status === 'error' }">
            <template v-if="item.status === 'compressing'">Crunching with MoMo engine...</template>
            <template v-else-if="item.status === 'completed'">Optimized successfully</template>
            <template v-else-if="item.status === 'error'">{{ item.errorMsg || 'Compression timed out (>10s) or failed. Please try again.' }}</template>
          </span>
        </div>

        <!-- Compressed Size & Savings Badge -->
        <div class="item-metrics">
          <template v-if="item.status === 'completed'">
            <div class="item-new-size">{{ formatBytes(item.compressedSizeBytes) }}</div>
            <div class="savings-pill">-{{ item.savedPercent }}%</div>
          </template>
          <template v-else-if="item.status === 'compressing'">
            <span style="font-size: 0.8rem; color: var(--text-muted);">...</span>
          </template>
          <template v-else>
            <div class="error-badge" title="Compression timed out or failed">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              <span>Failed</span>
            </div>
          </template>
        </div>

        <!-- Action Buttons (Download / Retry) -->
        <div class="item-actions">
          <button
            v-if="item.status === 'completed'"
            class="btn-item-download"
            @click="downloadItem(item)"
            title="Download compressed image"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            <span>Save</span>
          </button>

          <button
            v-else-if="item.status === 'error'"
            class="btn-item-retry"
            @click="retryItem(item)"
            title="Retry compression"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M23 4v6h-6"></path>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
            </svg>
            <span>Retry</span>
          </button>
        </div>

        <!-- Remove Button -->
        <button
          class="btn-item-remove"
          @click="removeItem(item.id)"
          title="Remove from queue"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
    </div>

    <!-- Image Comparison Modal -->
    <div v-if="activeComparison" class="modal-overlay" @click.self="closeComparison">
      <div class="modal-content">
        <div class="modal-header">
          <div>
            <h3 class="modal-title">Before & After Inspection</h3>
            <p style="font-size: 0.82rem; color: var(--text-secondary); margin: 0;">{{ activeComparison.name }}</p>
          </div>
          <button class="btn-item-remove" @click="closeComparison">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div class="modal-comparison-grid">
          <div class="preview-card">
            <div class="preview-title">Original ({{ formatBytes(activeComparison.originalSizeBytes) }})</div>
            <div class="preview-img-container">
              <img :src="activeComparison.thumbUrl" alt="Original Preview" class="preview-img" />
            </div>
          </div>
          <div class="preview-card">
            <div class="preview-title">
              MoMo Compressed ({{ formatBytes(activeComparison.compressedSizeBytes) }})
              <span class="savings-pill" style="margin-left: 8px;">-{{ activeComparison.savedPercent }}%</span>
            </div>
            <div class="preview-img-container">
              <img :src="activeComparison.dataUrl || activeComparison.thumbUrl" alt="Compressed Preview" class="preview-img" />
            </div>
          </div>
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 10px;">
          <button class="btn-secondary" @click="closeComparison">Close</button>
          <button class="btn-primary" @click="downloadItem(activeComparison)">
            Download Compressed File
          </button>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="app-footer">
      <p>White Buffalo MoMo Tool Suite · Phase 1: Image Compressor</p>
      <div class="footer-ecosystem-links">
        <span>Upcoming: PDF Compressor</span>
        <span>•</span>
        <span>PNG to PDF Converter</span>
      </div>
      <p style="font-size: 0.75rem; color: var(--text-muted); margin-top: 4px;">
        Decoupled Microservice Architecture · Fast in-memory processing · Apple Silicon & Linux VPS ready
      </p>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import JSZip from 'jszip'

const fileInput = ref(null)
const isDragging = ref(false)
const quality = ref(80)
const fileQueue = ref([])
const activeComparison = ref(null)
const isZipping = ref(false)

// Set preset quality
const setQuality = (val) => {
  quality.value = val
}

const triggerFileInput = () => {
  if (fileInput.value) {
    fileInput.value.click()
  }
}

const handleDragOver = () => {
  isDragging.value = true
}

const handleDragLeave = () => {
  isDragging.value = false
}

const handleDrop = (e) => {
  isDragging.value = false
  const files = Array.from(e.dataTransfer.files)
  processFiles(files)
}

const handleFileSelect = (e) => {
  const files = Array.from(e.target.files)
  processFiles(files)
  if (e.target) {
    e.target.value = ''
  }
}

// Format byte units
const formatBytes = (bytes, decimals = 1) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

// Add files to queue and trigger compression
const processFiles = (files) => {
  const validFiles = files.filter(f => {
    return f.type.startsWith('image/') || /\.(png|jpe?g|webp|gif)$/i.test(f.name)
  })

  validFiles.forEach(file => {
    // Explicitly make the item reactive so mutations trigger Vue 3 updates
    const item = reactive({
      id: `${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
      file,
      name: file.name,
      originalSizeBytes: file.size,
      thumbUrl: URL.createObjectURL(file),
      status: 'compressing',
      compressedSizeBytes: 0,
      savedBytes: 0,
      savedPercent: 0,
      dataUrl: null,
      mimeType: file.type || 'image/png',
      errorMsg: null,
    })
    fileQueue.value.unshift(item)
    compressItem(item)
  })
}

// Active abort controllers map to handle cancellations and 10s timeouts
const activeControllers = new Map()

// Call backend /api/compress with strict 10s timeout
const compressItem = async (item) => {
  // Guarantee we mutate the reactive instance tracked by Vue
  const targetItem = fileQueue.value.find(i => i.id === item.id) || item

  // Cancel previous pending request if any
  if (activeControllers.has(targetItem.id)) {
    try {
      activeControllers.get(targetItem.id).abort('CANCELLED')
    } catch (_) {}
    activeControllers.delete(targetItem.id)
  }

  const controller = new AbortController()
  activeControllers.set(targetItem.id, controller)

  let timedOut = false
  // Explicit 10-second request timeout
  const timeoutId = setTimeout(() => {
    timedOut = true
    try {
      controller.abort('TIMEOUT')
    } catch (_) {}
  }, 10000)

  try {
    const formData = new FormData()
    formData.append('file', targetItem.file)

    const response = await fetch(`/api/compress?quality=${quality.value}`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    })

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.detail || `Server error (${response.status})`)
    }

    const data = await response.json()
    targetItem.status = 'completed'
    targetItem.compressedSizeBytes = data.compressed_size
    targetItem.savedBytes = data.saved_bytes
    targetItem.savedPercent = data.saved_percent
    targetItem.dataUrl = data.data_url
    targetItem.mimeType = data.mime_type
    targetItem.errorMsg = null
  } catch (err) {
    targetItem.status = 'error'
    if (timedOut || err.name === 'AbortError' || err === 'TIMEOUT') {
      targetItem.errorMsg = 'Compression timed out (>10s) or failed. Please try again.'
    } else {
      targetItem.errorMsg = err.message || 'Compression timed out (>10s) or failed. Please try again.'
    }
  } finally {
    clearTimeout(timeoutId)
    activeControllers.delete(targetItem.id)
  }
}

// Retry failed item
const retryItem = (item) => {
  const targetItem = fileQueue.value.find(i => i.id === item.id) || item
  targetItem.status = 'compressing'
  targetItem.errorMsg = null
  compressItem(targetItem)
}

// Download single item
const downloadItem = (item) => {
  if (!item.dataUrl) return
  const a = document.createElement('a')
  a.href = item.dataUrl
  a.download = `compressed_${item.name}`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

// Download all completed as ZIP
const downloadAllAsZip = async () => {
  const completed = fileQueue.value.filter(i => i.status === 'completed' && i.dataUrl)
  if (completed.length === 0) return

  isZipping.value = true
  try {
    const zip = new JSZip()
    completed.forEach(item => {
      // Extract base64 part
      const base64Data = item.dataUrl.split(',')[1]
      zip.file(`compressed_${item.name}`, base64Data, { base64: true })
    })

    const content = await zip.generateAsync({ type: 'blob' })
    const zipUrl = URL.createObjectURL(content)
    const a = document.createElement('a')
    a.href = zipUrl
    a.download = `momo_compressed_images_${Date.now()}.zip`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(zipUrl)
  } catch (err) {
    console.error('Batch ZIP creation failed:', err)
  } finally {
    isZipping.value = false
  }
}

const removeItem = (id) => {
  if (activeControllers.has(id)) {
    try {
      activeControllers.get(id).abort('REMOVED')
    } catch (_) {}
    activeControllers.delete(id)
  }
  const index = fileQueue.value.findIndex(i => i.id === id)
  if (index !== -1) {
    if (fileQueue.value[index].thumbUrl) {
      URL.revokeObjectURL(fileQueue.value[index].thumbUrl)
    }
    fileQueue.value.splice(index, 1)
  }
}

const clearAll = () => {
  activeControllers.forEach(ctrl => {
    try {
      ctrl.abort('CLEAR_ALL')
    } catch (_) {}
  })
  activeControllers.clear()
  fileQueue.value.forEach(item => {
    if (item.thumbUrl) URL.revokeObjectURL(item.thumbUrl)
  })
  fileQueue.value = []
  activeComparison.value = null
}

const openComparison = (item) => {
  if (item.status === 'completed') {
    activeComparison.value = item
  }
}

const closeComparison = () => {
  activeComparison.value = null
}

// Summary Metrics
const completedCount = computed(() => {
  return fileQueue.value.filter(i => i.status === 'completed').length
})

const totalSavedBytes = computed(() => {
  return fileQueue.value
    .filter(i => i.status === 'completed')
    .reduce((sum, i) => sum + i.savedBytes, 0)
})

const totalSavingsPercent = computed(() => {
  const completed = fileQueue.value.filter(i => i.status === 'completed')
  if (completed.length === 0) return 0
  const origTotal = completed.reduce((sum, i) => sum + i.originalSizeBytes, 0)
  const savedTotal = completed.reduce((sum, i) => sum + i.savedBytes, 0)
  return origTotal > 0 ? ((savedTotal / origTotal) * 100).toFixed(1) : 0
})
</script>

<template>
  <div class="admin-panel-wrapper">
    <div class="admin-panel">
      <!-- Clinical Control Center Header -->
      <div class="admin-header">
        <div class="title-group">
          <div class="header-icon-wrapper">🔬</div>
          <div class="title-text">
            <h2>知识库中央控制台</h2>
            <span class="subtitle">HIS RAG / KNOWLEDGE DATA CONSOLE</span>
          </div>
        </div>
        <button @click="$emit('close')" class="close-btn">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
          退出控制台 / EXIT
        </button>
      </div>
      
      <!-- 工作台区域 -->
      <div class="admin-content">
        <!-- 统计面板 -->
        <div class="dashboard-section">
          <div class="section-header">
            <h3>📊 知识库实时检索统计 / CORE METRICS</h3>
            <button @click="fetchStats" class="refresh-btn">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
              刷新数据
            </button>
          </div>
          
          <div v-if="stats" class="stats-grid">
            <div class="stat-card primary" @click="viewChunks('medical_kb')" title="点击查看科普知识库区块">
              <div class="stat-icon">📗</div>
              <div class="stat-info">
                <span class="label">健康科普文献库</span>
                <span class="sub-label">medical_kb (Vector DB)</span>
              </div>
              <div class="value-wrapper">
                <span class="value">{{ stats.medical_kb_count || 0 }}</span>
                <span class="unit">Chunks</span>
              </div>
            </div>
            
            <div class="stat-card warning" @click="viewChunks('triage_kb')" title="点击查看分诊规则库区块">
              <div class="stat-icon">🚨</div>
              <div class="stat-info">
                <span class="label">红旗分诊规则库</span>
                <span class="sub-label">triage_kb (Vector DB)</span>
              </div>
              <div class="value-wrapper">
                <span class="value">{{ stats.triage_kb_count || 0 }}</span>
                <span class="unit">Chunks</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 上传面板 -->
        <div class="upload-section">
          <div class="section-header">
            <h3>📥 医疗指南与指南文献解析入库 / INGESTION PORTAL</h3>
          </div>
          
          <div class="upload-form">
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">目标存储知识库类别 / TARGET COLLECTION</label>
                <div class="custom-select-wrapper">
                  <select v-model="uploadCollection" class="custom-select">
                    <option value="medical_kb">📗 健康科普库 (用于常规疾病、科室科普问答)</option>
                    <option value="triage_kb">🚨 分诊规则库 (用于高危症状拦截、红旗挂号提示)</option>
                  </select>
                </div>
              </div>
            </div>
            
            <div class="file-drop-area" :class="{ 'has-file': fileSelected }">
              <div class="file-icon-pulse">
                <svg v-if="!fileSelected" xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="upload-icon-svg"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="file-selected-svg"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
              </div>
              <p v-if="!fileSelected" class="drop-help">拖拽文件到这里，或点击下方按钮选择本地文件<br/><span class="file-formats">支持 .md, .txt, .pdf, .docx 规范医疗文献资料</span></p>
              <div v-else class="file-detail">
                <p class="file-name">{{ selectedFileName }}</p>
                <span class="ready-badge">已就绪 / READY TO INGEST</span>
              </div>
              <input type="file" ref="fileInput" @change="onFileChange" accept=".md,.txt,.pdf,.docx" class="file-input-hidden" />
              <button class="browse-btn" @click="$refs.fileInput.click()">选择本地文件</button>
            </div>
            
            <button @click="uploadFile" class="submit-btn" :disabled="isUploading || !fileSelected">
              <span v-if="isUploading" class="loader"></span>
              {{ isUploading ? '文献深度解析与多维向量化中...' : '开始解析并导入向量库 / START INGEST' }}
            </button>
            
            <transition name="fade">
              <div v-if="uploadMessage" class="status-message" :class="uploadSuccess ? 'success' : 'error'">
                <span class="status-icon">{{ uploadSuccess ? '✅' : '⚠️' }}</span>
                <span class="status-text-content">{{ uploadMessage }}</span>
              </div>
            </transition>
          </div>
        </div>
      </div>
      
      <!-- Chunk Viewer Modal -->
      <Teleport to="body">
        <div v-if="showChunkModal" class="chunk-modal-overlay" @click.self="showChunkModal = false">
          <div class="chunk-modal">
            <div class="modal-header">
              <div class="modal-title-group">
                <span class="modal-badge">DATABASE INSPECTOR</span>
                <h3>ChromaDB 向量区块检视器 - {{ currentViewCollection }}</h3>
              </div>
              <button @click="showChunkModal = false" class="modal-close">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </div>
            <div class="modal-body">
              <div v-if="isFetchingChunks" class="chunk-loader">
                <span class="loader-spinner"></span>
                <p>正在读取 ChromaDB 索引区块中...</p>
              </div>
              <div v-else-if="chunksData.length === 0" class="empty-state">
                <div class="empty-icon">📭</div>
                <p>当前向量知识库集合尚无有效区块，请先导入文献资料。</p>
              </div>
              <div v-else class="chunk-list">
                <div v-for="(chunk, idx) in chunksData" :key="idx" class="chunk-item">
                  <div class="chunk-meta">
                    <span class="source-badge">📄 {{ chunk.metadata.source || 'Unknown' }}</span>
                    <span class="part-badge" v-if="chunk.metadata.part">ID Part {{ chunk.metadata.part }}</span>
                    <span class="section-badge" v-if="chunk.metadata.section">{{ chunk.metadata.section }}</span>
                  </div>
                  <div class="chunk-text">{{ chunk.content }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Teleport>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const emit = defineEmits(['close'])

const authHeader = ref('Basic YWRtaW46YWRtaW4=') // Hardcoded admin:admin Basic Auth

const stats = ref(null)
const uploadCollection = ref('medical_kb')
const fileInput = ref(null)
const isUploading = ref(false)
const uploadMessage = ref('')
const uploadSuccess = ref(false)
const fileSelected = ref(false)
const selectedFileName = ref('')

// Chunk Viewer State
const showChunkModal = ref(false)
const chunksData = ref([])
const isFetchingChunks = ref(false)
const currentViewCollection = ref('')

const viewChunks = async (collection) => {
  showChunkModal.value = true
  currentViewCollection.value = collection
  isFetchingChunks.value = true
  chunksData.value = []
  
  try {
    const res = await fetch(`/api/knowledge/chunks?collection=${collection}`, {
      headers: { 'Authorization': authHeader.value }
    })
    if (res.ok) {
      const data = await res.json()
      chunksData.value = data.chunks || []
    }
  } catch (err) {
    console.error("Failed to fetch chunks", err)
  } finally {
    isFetchingChunks.value = false
  }
}

const onFileChange = (e) => {
  const file = e.target.files[0]
  if (file) {
    fileSelected.value = true
    selectedFileName.value = file.name
  } else {
    fileSelected.value = false
    selectedFileName.value = ''
  }
}

onMounted(() => {
  fetchStats()
})

const fetchStats = async () => {
  try {
    const res = await fetch('/api/knowledge/stats', {
      headers: { 'Authorization': authHeader.value }
    })
    if (res.ok) {
      stats.value = await res.json()
    }
  } catch (e) {
    console.error("Failed to fetch stats", e)
  }
}

const uploadFile = async () => {
  const file = fileInput.value?.files[0]
  if (!file) return
  
  isUploading.value = true
  uploadMessage.value = ''
  
  const formData = new FormData()
  formData.append('file', file)
  formData.append('collection', uploadCollection.value)
  
  try {
    const res = await fetch('/api/knowledge/upload', {
      method: 'POST',
      headers: { 'Authorization': authHeader.value },
      body: formData
    })
    
    const data = await res.json()
    if (res.ok) {
      uploadSuccess.value = true
      uploadMessage.value = `导入向量库成功！该文献已被自动解析并切分为 ${data.chunks_added} 个多维语义区块。`
      fetchStats()
      // reset file
      fileInput.value.value = ''
      fileSelected.value = false
    } else {
      uploadSuccess.value = false
      uploadMessage.value = data.detail || "文献导入失败：服务解析异常"
    }
  } catch (e) {
    uploadSuccess.value = false
    uploadMessage.value = "网络异常：大文件传输中断"
  } finally {
    isUploading.value = false
  }
}
</script>

<style scoped>
.admin-panel-wrapper {
  width: 100%;
  height: 100%;
  background: #f8fafc;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  overflow-y: auto;
  padding: 40px 20px;
}

.admin-panel-wrapper::-webkit-scrollbar {
  width: 6px;
}
.admin-panel-wrapper::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
  border-radius: 6px;
}

.admin-panel {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  width: 100%;
  max-width: 1000px;
  border-radius: 16px;
  box-shadow: 
    0 4px 6px -1px rgba(15, 23, 42, 0.03),
    0 20px 40px -10px rgba(15, 23, 42, 0.05),
    inset 0 1px 0 white;
  border: 1px solid rgba(226, 232, 240, 0.8);
  overflow: hidden;
  animation: slideUpFade 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.admin-header {
  background: linear-gradient(135deg, #0d9488, #0f766e);
  padding: 22px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
}

.title-group {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-icon-wrapper {
  width: 44px;
  height: 44px;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.title-text h2 {
  margin: 0 0 2px 0;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.subtitle {
  font-size: 11px;
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 0.05em;
}

.close-btn {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  padding: 10px 18px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13.5px;
  font-weight: 600;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
}

.admin-content {
  padding: 32px;
}

/* --- Sections --- */
.dashboard-section {
  margin-bottom: 36px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 10px;
}

.section-header h3 {
  margin: 0;
  color: #0f172a;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: white;
  border: 1px solid #cbd5e1;
  padding: 8px 14px;
  border-radius: 6px;
  font-size: 12.5px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover {
  background: #f8fafc;
  color: var(--primary);
  border-color: var(--primary);
}

/* --- Stats Grid --- */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.stat-card {
  padding: 24px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.02);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px -5px rgba(15, 23, 42, 0.04), 0 4px 6px -2px rgba(15, 23, 42, 0.02);
}

.stat-card.primary {
  border-left: 4px solid var(--primary);
}
.stat-card.primary:hover {
  border-color: var(--primary);
}

.stat-card.warning {
  border-left: 4px solid #f59e0b;
}
.stat-card.warning:hover {
  border-color: #f59e0b;
}

.stat-icon {
  font-size: 26px;
  margin-right: 18px;
  background: #f1f5f9;
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  transition: background-color 0.2s;
}

.stat-card:hover .stat-icon {
  background: #e2e8f0;
}

.stat-info {
  flex: 1;
}

.stat-info .label {
  font-weight: 700;
  color: #1e293b;
  font-size: 14.5px;
  display: block;
}

.stat-info .sub-label {
  font-size: 11.5px;
  color: #94a3b8;
  font-family: ui-monospace, SFMono-Regular, monospace;
}

.value-wrapper {
  text-align: right;
}

.value-wrapper .value {
  font-size: 32px;
  font-weight: 800;
  color: #0f172a;
  display: block;
  font-family: ui-monospace, SFMono-Regular, monospace;
  line-height: 1;
}

.value-wrapper .unit {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 600;
  text-transform: uppercase;
}

/* --- Ingestion upload portal --- */
.upload-section {
  background: #ffffff;
  padding: 24px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.02);
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 11px;
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-weight: 700;
  color: #64748b;
  margin-bottom: 8px;
  letter-spacing: 0.05em;
}

.custom-select-wrapper {
  position: relative;
}

.custom-select {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  outline: none;
  font-weight: 500;
  color: #334155;
  transition: all 0.2s;
}

.custom-select:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.1);
}

.file-drop-area {
  margin-top: 20px;
  border: 2px dashed #cbd5e1;
  border-radius: 10px;
  padding: 36px;
  text-align: center;
  background: #f8fafc;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.file-drop-area.has-file {
  border-color: var(--primary);
  background: rgba(13, 148, 136, 0.02);
}

.file-icon-pulse {
  font-size: 36px;
  margin-bottom: 12px;
  color: #cbd5e1;
  display: flex;
  justify-content: center;
}

.file-drop-area.has-file .file-icon-pulse {
  color: var(--primary);
}

.drop-help {
  color: #64748b;
  font-size: 13.5px;
  line-height: 1.5;
  margin: 0 0 16px 0;
}

.file-formats {
  font-size: 11.5px;
  color: #94a3b8;
}

.file-detail {
  margin-bottom: 16px;
}

.file-name {
  font-weight: 700;
  color: var(--primary);
  font-size: 15px;
  margin: 0 0 4px 0;
}

.ready-badge {
  font-size: 10px;
  font-family: ui-monospace, SFMono-Regular, monospace;
  background: #ecfdf5;
  color: #047857;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 700;
}

.file-input-hidden {
  display: none;
}

.browse-btn {
  background: white;
  border: 1px solid #cbd5e1;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  color: #475569;
  transition: all 0.2s;
}

.browse-btn:hover {
  background: #f1f5f9;
  border-color: #94a3b8;
}

.submit-btn {
  margin-top: 24px;
  width: 100%;
  padding: 14px;
  background: var(--primary-gradient);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  transition: all 0.25s;
  box-shadow: 0 4px 10px rgba(13, 148, 136, 0.15);
}

.submit-btn:disabled {
  background: #cbd5e1;
  box-shadow: none;
  cursor: not-allowed;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(13, 148, 136, 0.25);
}

.status-message {
  margin-top: 16px;
  padding: 12px 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  font-weight: 600;
}

.status-message.success {
  background: #ecfdf5;
  color: #065f46;
  border: 1px solid #a7f3d0;
}

.status-message.error {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

/* --- Chunk Inspector Modal (Modern Glass overlay) --- */
.chunk-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.3);
  backdrop-filter: blur(12px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.chunk-modal {
  width: 90%;
  max-width: 820px;
  height: 80vh;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: 
    0 10px 25px -5px rgba(15, 23, 42, 0.1),
    0 20px 50px -12px rgba(15, 23, 42, 0.15);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.8);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.4);
}

.modal-badge {
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-size: 9px;
  font-weight: 700;
  background: var(--primary);
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  letter-spacing: 0.05em;
  display: inline-block;
  margin-bottom: 4px;
}

.modal-title-group h3 {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  cursor: pointer;
  color: #94a3b8;
  padding: 6px;
  border-radius: 6px;
  transition: 0.2s;
  display: flex;
  align-items: center;
}

.modal-close:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.modal-body::-webkit-scrollbar {
  width: 5px;
}
.modal-body::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
  border-radius: 4px;
}

.chunk-loader {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 40px;
  color: #64748b;
}

.loader-spinner {
  border: 3px solid rgba(13, 148, 136, 0.1);
  border-top: 3px solid var(--primary);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  animation: spin 1s linear infinite;
}

.empty-state {
  text-align: center;
  padding: 60px 40px;
  color: #94a3b8;
}

.empty-icon {
  font-size: 36px;
  margin-bottom: 8px;
}

.chunk-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.chunk-item {
  background: #ffffff;
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 10px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.01);
  transition: all 0.2s ease;
}

.chunk-item:hover {
  border-color: rgba(13, 148, 136, 0.3);
  box-shadow: var(--shadow-md);
}

.chunk-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.chunk-meta span {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, monospace;
}

.source-badge {
  background: #f0fdfa;
  color: #0f766e;
  border: 1px solid rgba(13, 148, 136, 0.15);
}

.part-badge {
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid rgba(29, 78, 216, 0.1);
}

.section-badge {
  background: #fdf2f8;
  color: #be185d;
  border: 1px solid rgba(190, 24, 93, 0.1);
}

.chunk-text {
  font-size: 13.5px;
  color: #334155;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
  background: #f8fafc;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid rgba(226,232,240,0.5);
}

/* Ingestion animations */
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loader {
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  animation: spin 1s linear infinite;
}

@keyframes slideUpFade {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.fade-enter-active, .fade-leave-active {
  transition: all 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>

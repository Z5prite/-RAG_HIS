<template>
  <div class="admin-panel-wrapper">
    <div class="admin-panel">
      <div class="admin-header">
        <div class="title-group">
          <h2>⚕️ 知识库中央控制台</h2>
          <span class="subtitle">HIS RAG - Knowledge Base Management</span>
        </div>
        <button @click="$emit('close')" class="close-btn">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
          退出系统
        </button>
      </div>
      
      <!-- 工作台区域 -->
      <div class="admin-content">
        <!-- 统计面板 -->
        <div class="dashboard-section">
          <div class="section-header">
            <h3>📊 知识库数据大屏</h3>
            <button @click="fetchStats" class="refresh-btn">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
              刷新数据
            </button>
          </div>
          
          <div v-if="stats" class="stats-grid">
            <div class="stat-card primary" @click="viewChunks('medical_kb')" title="点击查看科普知识库区块">
              <div class="stat-icon">📚</div>
              <div class="stat-info">
                <span class="label">健康科普知识库</span>
                <span class="sub-label">medical_kb</span>
              </div>
              <div class="value-wrapper">
                <span class="value">{{ stats.medical_kb_count || 0 }}</span>
                <span class="unit">区块</span>
              </div>
            </div>
            
            <div class="stat-card warning" @click="viewChunks('triage_kb')" title="点击查看分诊规则库区块">
              <div class="stat-icon">🏥</div>
              <div class="stat-info">
                <span class="label">红旗分诊规则库</span>
                <span class="sub-label">triage_kb</span>
              </div>
              <div class="value-wrapper">
                <span class="value">{{ stats.triage_kb_count || 0 }}</span>
                <span class="unit">区块</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 上传面板 -->
        <div class="upload-section">
          <div class="section-header">
            <h3>📤 导入医疗文献资料</h3>
          </div>
          
          <div class="upload-form">
            <div class="form-row">
              <div class="form-group">
                <label>请选择目标知识库类型：</label>
                <div class="custom-select">
                  <select v-model="uploadCollection">
                    <option value="medical_kb">📗 健康科普库 (用于常规疾病、用药问答)</option>
                    <option value="triage_kb">🚨 分诊规则库 (用于高危症状拦截、科室推荐)</option>
                  </select>
                </div>
              </div>
            </div>
            
            <div class="file-drop-area" :class="{ 'has-file': fileSelected }">
              <div class="file-icon">📄</div>
              <p v-if="!fileSelected">支持上传 .md, .txt, .pdf, .docx 格式医疗文档</p>
              <p v-else class="file-name">{{ selectedFileName }}</p>
              <input type="file" ref="fileInput" @change="onFileChange" accept=".md,.txt,.pdf,.docx" class="file-input-hidden" />
              <button class="browse-btn" @click="$refs.fileInput.click()">选择文件</button>
            </div>
            
            <button @click="uploadFile" class="submit-btn" :disabled="isUploading || !fileSelected">
              <span v-if="isUploading" class="loader"></span>
              {{ isUploading ? '文档解析并向量化中...' : '开始入库' }}
            </button>
            
            <div v-if="uploadMessage" class="status-message" :class="uploadSuccess ? 'success' : 'error'">
              <span class="status-icon">{{ uploadSuccess ? '✅' : '❌' }}</span>
              {{ uploadMessage }}
            </div>
          </div>
        </div>
      </div>
      
      <!-- Chunk Viewer Modal -->
      <Teleport to="body">
        <div v-if="showChunkModal" class="chunk-modal-overlay" @click.self="showChunkModal = false">
        <div class="chunk-modal">
          <div class="modal-header">
            <h3>🔬 区块监视器 ({{ currentViewCollection }})</h3>
            <button @click="showChunkModal = false" class="close-btn modal-close">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>
          <div class="modal-body">
            <div v-if="isFetchingChunks" class="chunk-loader">
              <span class="loader dark"></span>
              <p>正在从 Chroma 加载区块数据...</p>
            </div>
            <div v-else-if="chunksData.length === 0" class="empty-state">
              当前知识库没有区块数据。
            </div>
            <div v-else class="chunk-list">
              <div v-for="(chunk, idx) in chunksData" :key="idx" class="chunk-item">
                <div class="chunk-meta">
                  <span class="source-badge">📄 {{ chunk.metadata.source || 'Unknown' }}</span>
                  <span class="part-badge" v-if="chunk.metadata.part">Part {{ chunk.metadata.part }}</span>
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
      uploadMessage.value = `入库成功！文献被提取为 ${data.chunks_added} 个语义区块。`
      fetchStats()
      // reset file
      fileInput.value.value = ''
      fileSelected.value = false
    } else {
      uploadSuccess.value = false
      uploadMessage.value = data.detail || "入库失败：发生未知错误"
    }
  } catch (e) {
    uploadSuccess.value = false
    uploadMessage.value = "网络异常：文件传输中断"
  } finally {
    isUploading.value = false
  }
}
</script>

<style scoped>
.admin-panel-wrapper {
  width: 100%;
  height: 100%;
  background: transparent;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  overflow-y: auto;
  padding: 40px 20px;
}
.admin-panel-wrapper::-webkit-scrollbar { width: 6px; }
.admin-panel-wrapper::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.3); border-radius: 6px; }

.admin-panel {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  width: 100%;
  max-width: 960px;
  border-radius: 20px;
  box-shadow: var(--shadow-md);
  border: 1px solid rgba(255, 255, 255, 0.8);
  overflow: hidden;
  animation: slideUpFade 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.admin-header {
  background: var(--primary-gradient);
  padding: 24px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
}
.title-group h2 {
  margin: 0 0 6px 0;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.subtitle {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
}
.close-btn {
  background: rgba(255,255,255,0.15);
  border: 1px solid rgba(255,255,255,0.3);
  color: white;
  padding: 10px 18px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.25s;
  font-size: 14px;
  font-weight: 600;
}
.close-btn:hover { background: rgba(255,255,255,0.25); transform: translateY(-1px); }

/* Dashboard Content */
.admin-content {
  padding: 32px;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.section-header h3 {
  margin: 0;
  color: #0f172a;
  font-size: 18px;
  font-weight: 700;
}
.refresh-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: white;
  border: 1px solid #cbd5e1;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}
.refresh-btn:hover { background: #f8fafc; color: var(--primary); border-color: var(--primary); }

.dashboard-section {
  margin-bottom: 40px;
}
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
.stat-card {
  padding: 24px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  border: 1px solid rgba(255,255,255,0.6);
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 15px rgba(0,0,0,0.03);
  transition: transform 0.2s, box-shadow 0.2s;
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.05);
}
.stat-card.primary { border-left: 5px solid var(--primary); }
.stat-card.warning { border-left: 5px solid #f59e0b; }

.stat-icon {
  font-size: 32px;
  margin-right: 20px;
  background: #ffffff;
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.04);
}
.stat-info { flex: 1; display: flex; flex-direction: column; }
.stat-info .label { font-weight: 700; color: #1e293b; font-size: 16px; margin-bottom: 4px; }
.stat-info .sub-label { font-size: 13px; color: #64748b; font-family: monospace; font-weight: 500; }
.value-wrapper { text-align: right; }
.value-wrapper .value { font-size: 36px; font-weight: 800; color: #0f172a; display: block; letter-spacing: -1px; }
.value-wrapper .unit { font-size: 13px; color: #94a3b8; font-weight: 600; }

/* Upload Section */
.upload-section {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
  padding: 32px;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.6);
  box-shadow: 0 4px 15px rgba(0,0,0,0.03);
}
.form-group label {
  display: block;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 12px;
}
.custom-select select {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  font-size: 15px;
  background: white;
  outline: none;
  font-weight: 500;
  color: #334155;
  transition: all 0.2s;
}
.custom-select select:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.15); }

.file-drop-area {
  margin-top: 24px;
  border: 2px dashed #cbd5e1;
  border-radius: 16px;
  padding: 48px;
  text-align: center;
  background: rgba(255,255,255,0.5);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.file-drop-area.has-file {
  border-color: var(--primary);
  background: rgba(13, 148, 136, 0.04);
}
.file-icon { font-size: 42px; margin-bottom: 16px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.05)); }
.file-drop-area p { color: #64748b; margin-bottom: 20px; font-weight: 500; }
.file-name { font-weight: 700; color: var(--primary) !important; font-size: 16px; }
.file-input-hidden { display: none; }
.browse-btn {
  background: white;
  border: 1px solid #cbd5e1;
  padding: 10px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  color: #334155;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}
.browse-btn:hover { background: #f1f5f9; border-color: #94a3b8; }

.submit-btn {
  margin-top: 32px;
  width: 100%;
  padding: 16px;
  background: var(--primary-gradient);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3);
}
.submit-btn:disabled { background: #cbd5e1; box-shadow: none; cursor: not-allowed; }
.submit-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(13, 148, 136, 0.4); }

.status-message {
  margin-top: 20px;
  padding: 16px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
  font-size: 14px;
}
.status-message.success { background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0; }
.status-message.error { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }

.loader {
  border: 2px solid rgba(255,255,255,0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

.chunk-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(8px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.2s ease-out;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.chunk-modal {
  width: 90%;
  max-width: 800px;
  max-height: 85vh;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(255,255,255, 1);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  padding: 24px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.8);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.5);
}
.modal-header h3 { font-size: 18px; font-weight: 700; color: #1e293b; margin: 0; }
.modal-close { background: none; border: none; cursor: pointer; color: #64748b; padding: 8px; border-radius: 8px; transition: 0.2s; }
.modal-close:hover { background: #f1f5f9; color: #0f172a; }

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}
.modal-body::-webkit-scrollbar { width: 6px; }
.modal-body::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.3); border-radius: 6px; }

.chunk-loader { display: flex; flex-direction: column; align-items: center; gap: 16px; padding: 40px; color: #64748b; }
.loader.dark { border-color: rgba(15, 23, 42, 0.1); border-top-color: #0d9488; }
.empty-state { text-align: center; padding: 40px; color: #94a3b8; font-size: 15px; }

.chunk-list { display: flex; flex-direction: column; gap: 16px; }
.chunk-item {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
  transition: all 0.2s;
}
.chunk-item:hover { border-color: #99f6e4; box-shadow: 0 4px 12px rgba(13, 148, 136, 0.08); }
.chunk-meta { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.chunk-meta span { font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 6px; }
.source-badge { background: #f0fdfa; color: #0f766e; }
.part-badge { background: #eff6ff; color: #1d4ed8; }
.section-badge { background: #fdf2f8; color: #be185d; }
.chunk-text { font-size: 14px; color: #475569; line-height: 1.6; word-break: break-word; white-space: pre-wrap; }
</style>

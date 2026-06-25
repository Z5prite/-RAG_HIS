<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { marked } from 'marked'
import AdminPanel from './components/AdminPanel.vue'
import LoginScreen from './components/LoginScreen.vue'

const currentUserRole = ref(null) // 'admin' or 'user' or null
const sessions = ref([])
const activeSessionId = ref(null)
const messages = ref([])
const inputText = ref('')
const isGenerating = ref(false)
const messagesContainer = ref(null)
const showAdmin = ref(false)

// --------------------- Authentication ---------------------
const handleLogin = (role) => {
  currentUserRole.value = role
  if (role === 'admin') {
    showAdmin.value = true
  }
  fetchSessions()
}

const handleLogout = () => {
  currentUserRole.value = null
  showAdmin.value = false
  activeSessionId.value = null
  messages.value = []
  sessions.value = []
}

// --------------------- API Calls ---------------------
const fetchSessions = async () => {
  if (!currentUserRole.value) return
  try {
    const res = await fetch('/api/sessions')
    const data = await res.json()
    sessions.value = data.sessions || []
  } catch (err) {
    console.error('Failed to fetch sessions:', err)
  }
}

const loadSession = async (sessionId) => {
  try {
    const res = await fetch(`/api/sessions/${sessionId}/messages`)
    const data = await res.json()
    
    messages.value = data.messages.map(m => ({
      role: m.role,
      content: m.content,
      metadata: m.metadata
    }))
    scrollToBottom()
  } catch (err) {
    console.error('Failed to load session:', err)
  }
}

const deleteSession = async (sessionId, event) => {
  event.stopPropagation()
  if (!confirm('确定要彻底删除这条问诊记录吗？')) return
  try {
    const res = await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' })
    if (res.ok) {
      if (activeSessionId.value === sessionId) {
        activeSessionId.value = null
        messages.value = []
      }
      fetchSessions()
    }
  } catch (err) {
    console.error('Failed to delete session:', err)
  }
}

marked.use({ breaks: true, gfm: true })

const renderMarkdown = (text) => {
  if (!text) return ''
  return marked.parse(text)
}

// --------------------- Interactions ---------------------
const createNewChat = () => {
  activeSessionId.value = null
  messages.value = []
  showAdmin.value = false
}

const selectSession = (sessionId) => {
  activeSessionId.value = sessionId
  showAdmin.value = false
  loadSession(sessionId)
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || isGenerating.value) return

  messages.value.push({
    role: 'user',
    content: text,
    metadata: null
  })
  
  inputText.value = ''
  isGenerating.value = true
  
  const targetMsg = {
    role: 'assistant',
    content: '',
    metadata: {}
  }
  messages.value.push(targetMsg)
  scrollToBottom()

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        message: text, 
        session_id: activeSessionId.value 
      })
    })

    if (!res.ok) throw new Error('API request failed')

    const reader = res.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.slice(6)
          if (dataStr === '[DONE]') continue
          
          try {
            const parsed = JSON.parse(dataStr)
            if (parsed.type === 'chunk') {
              targetMsg.content += parsed.delta
              scrollToBottom()
            } else if (parsed.type === 'done') {
              if (parsed.meta) {
                targetMsg.metadata = { ...targetMsg.metadata, ...parsed.meta }
                targetMsg.content = targetMsg.content.replace(/<meta>[\s\S]*?<\/meta>/g, '').trim()
              }
              if (parsed.session_id && !activeSessionId.value) {
                activeSessionId.value = parsed.session_id
                fetchSessions()
              }
            }
          } catch (e) {
            console.error("Failed to parse SSE data", e, dataStr)
          }
        }
      }
    }
  } catch (err) {
    targetMsg.content += "\n\n[网络请求失败，请稍后重试]"
  } finally {
    isGenerating.value = false
    scrollToBottom()
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}
</script>

<template>
  <LoginScreen v-if="!currentUserRole" @login="handleLogin" />
  
  <!-- 管理员专属全屏控制台 -->
  <div v-else-if="currentUserRole === 'admin'" class="app-container" style="background: #f1f5f9;">
    <AdminPanel @close="handleLogout" />
  </div>

  <!-- 普通医生/患者接诊台 -->
  <div v-else class="app-container">
    <!-- 侧边栏: Deep Medical Blue -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="brand">
          <span class="brand-icon">⚕️</span>
          <h2>RAG of HIS</h2>
        </div>
        <button class="new-chat-btn" @click="createNewChat">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          新建问诊
        </button>
      </div>
      
      <div class="session-list">
        <div class="session-group-title">历史问诊</div>
        <div 
          v-for="s in sessions" 
          :key="s.session_id"
          class="session-item"
          :class="{ active: s.session_id === activeSessionId }"
          @click="selectSession(s.session_id)"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="session-icon"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
          <span class="session-title">{{ s.title || '无标题问诊' }}</span>
          <button class="session-delete-btn" @click="(e) => deleteSession(s.session_id, e)" title="删除记录">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
          </button>
        </div>
      </div>
      
      <div class="sidebar-footer">
        <!-- 登出按钮 -->
        <button class="logout-btn" @click="handleLogout">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
          退出系统 ({{ currentUserRole }})
        </button>
      </div>
    </aside>

    <!-- 主聊天区 -->
    <main class="main-content">
      <div class="chat-area">
        <header class="chat-header">
          <div class="header-title">智能分诊与健康助手</div>
          <div class="header-subtitle">基于院内知识库的 RAG AI 引擎</div>
        </header>
        
        <div class="messages-container" ref="messagesContainer">
          <!-- Welcome Message -->
          <div v-if="messages.length === 0" class="message-wrapper assistant">
            <div class="avatar">⚕️</div>
            <div class="message-bubble welcome-bubble">
              <h3>您好！我是您的智能数字医生。</h3>
              <p>我可以基于医院权威知识库为您提供：</p>
              <ul>
                <li><strong>症状分析与智能分诊：</strong> 告诉我您的不适，我会推荐就诊科室。</li>
                <li><strong>健康科普咨询：</strong> 解答常见疾病、用药与生活习惯问题。</li>
              </ul>
              <div class="disclaimer">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                <span>免责声明：我的回答仅供参考，不作为最终诊断和处方依据。<br/><strong>如遇突发危急重症，请立即前往急诊或拨打120。</strong></span>
              </div>
            </div>
          </div>

          <!-- Chat Messages -->
          <div 
            v-for="(msg, index) in messages" 
            :key="index"
            class="message-wrapper"
            :class="msg.role"
          >
            <div class="avatar" v-if="msg.role === 'assistant'">⚕️</div>
            
            <div class="message-content">
              <!-- AI 气泡 -->
              <div v-if="msg.role === 'assistant'" class="message-bubble ai-bubble">
                <div class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
                
                <!-- 处方笺式分诊卡片 -->
                <div v-if="msg.metadata && msg.metadata.department" class="triage-card" :class="getRiskClass(msg.metadata.risk)">
                  <div class="triage-header">
                    <span class="triage-icon">📋</span>
                    <h4>电子分诊建议单</h4>
                  </div>
                  <div class="triage-body">
                    <div class="triage-row">
                      <span class="triage-label">推荐就诊科室</span>
                      <span class="triage-value dept">{{ msg.metadata.department }}</span>
                    </div>
                    <div class="triage-row">
                      <span class="triage-label">评估风险等级</span>
                      <div class="risk-badge" :class="getRiskClass(msg.metadata.risk)">
                        <span class="pulse-dot" v-if="msg.metadata.risk?.includes('急诊') || msg.metadata.risk?.includes('高')"></span>
                        {{ msg.metadata.risk }}
                      </div>
                    </div>
                    <div class="triage-row suggestion" v-if="msg.metadata.suggestion">
                      <span class="triage-label">医嘱建议</span>
                      <p class="triage-value">{{ msg.metadata.suggestion }}</p>
                    </div>
                  </div>
                </div>

                <!-- 溯源面板 -->
                <details v-if="msg.metadata && msg.metadata.evidence && msg.metadata.evidence.length > 0" class="evidence-panel">
                  <summary class="evidence-summary">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>
                    查看引用的本地知识库 ({{ msg.metadata.evidence.length }} 条)
                  </summary>
                  <div class="evidence-content">
                    <div v-for="(ev, i) in msg.metadata.evidence" :key="i" class="evidence-item">
                      <div class="evidence-source">📄 {{ ev.source }} <span class="badge">{{ ev.section }}</span></div>
                      <div class="evidence-snippet">"{{ ev.snippet }}"</div>
                    </div>
                  </div>
                </details>
              </div>

              <!-- User 气泡 -->
              <div v-else class="message-bubble user-bubble">{{ msg.content.trim() }}</div>
            </div>
          </div>
        </div>
        
        <div class="input-area-wrapper">
          <div class="input-container">
            <input 
              v-model="inputText" 
              @keyup.enter="sendMessage"
              type="text" 
              class="chat-input" 
              placeholder="请输入您的症状描述，例如：最近总是头晕，偶尔心慌..." 
              :disabled="isGenerating"
            />
            <button class="send-btn" @click="sendMessage" :disabled="isGenerating || !inputText.trim()">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
            </button>
          </div>
          <div class="input-footer">基于大模型的医疗回答仅供参考，不作为最终诊断。</div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
// Helper for risk classes
export function getRiskClass(risk) {
  if (!risk) return 'risk-low';
  if (risk.includes('低')) return 'risk-low';
  if (risk.includes('中')) return 'risk-medium';
  if (risk.includes('高') || risk.includes('急诊')) return 'risk-high';
  return 'risk-low';
}
</script>

<style>
/* -------------------------------------
   全局重置与字体 (Bio-Tech Precision)
-------------------------------------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --primary: #0d9488;
  --primary-hover: #0f766e;
  --primary-gradient: linear-gradient(135deg, #0d9488, #0284c7);
  --bg-main: #f4f7fb;
  --bg-sidebar: rgba(255, 255, 255, 0.65);
  --text-main: #1e293b;
  --text-light: #64748b;
  --risk-low: #059669;
  --risk-med: #d97706;
  --risk-high: #dc2626;
  --shadow-sm: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
  --shadow-md: 0 10px 25px -5px rgba(0, 0, 0, 0.08), 0 8px 10px -6px rgba(0, 0, 0, 0.04);
}

body {
  margin: 0;
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  color: var(--text-main);
  background: linear-gradient(135deg, #f4f7fb 0%, #eef2f6 100%);
  height: 100vh;
  overflow: hidden;
}

.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  background: transparent;
}

/* -------------------------------------
   侧边栏 (Glassmorphism Sidebar)
-------------------------------------- */
.sidebar {
  width: 280px;
  background-color: var(--bg-sidebar);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  color: var(--text-main);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  border-right: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 4px 0 24px rgba(0,0,0,0.02);
  z-index: 20;
}

.sidebar-header {
  padding: 24px 20px 16px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 28px;
}
.brand-icon {
  font-size: 26px;
  filter: drop-shadow(0 2px 4px rgba(13,148,136,0.2));
}
.brand h2 {
  margin: 0;
  font-size: 19px;
  font-weight: 700;
  letter-spacing: 0.5px;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.new-chat-btn {
  width: 100%;
  padding: 12px;
  background: var(--primary-gradient);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.25);
}
.new-chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(13, 148, 136, 0.35);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px 16px;
}
.session-list::-webkit-scrollbar { width: 4px; }
.session-list::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.3); border-radius: 4px; }

.session-group-title {
  font-size: 12px;
  color: #94a3b8;
  margin: 16px 8px 8px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.session-item {
  padding: 12px 14px;
  margin-bottom: 6px;
  border-radius: 10px;
  cursor: pointer;
  color: #475569;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.2s;
  background: transparent;
  border: 1px solid transparent;
}
.session-item:hover {
  background: rgba(255, 255, 255, 0.8);
  border-color: rgba(255,255,255,1);
  box-shadow: 0 2px 6px rgba(0,0,0,0.02);
}
.session-item.active {
  background: #ffffff;
  color: #0f172a;
  font-weight: 600;
  border-color: #e2e8f0;
  box-shadow: var(--shadow-sm);
}
.session-icon { opacity: 0.5; }
.session-item.active .session-icon { opacity: 1; color: var(--primary); }
.session-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.session-delete-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.2s;
  flex-shrink: 0;
}
.session-item:hover .session-delete-btn {
  opacity: 1;
}
.session-delete-btn:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.sidebar-footer {
  padding: 20px 16px;
  background: linear-gradient(to top, rgba(255,255,255,0.8), transparent);
}

.logout-btn {
  width: 100%;
  padding: 12px;
  background: #ffffff;
  color: #ef4444;
  border: 1px solid #fecaca;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(239,68,68,0.05);
}
.logout-btn:hover {
  background: #fef2f2;
  border-color: #fca5a5;
  box-shadow: 0 4px 8px rgba(239,68,68,0.1);
}

/* -------------------------------------
   主工作区 (Main Content)
-------------------------------------- */
.main-content {
  flex: 1;
  display: flex;
  background-color: transparent;
  position: relative;
  padding: 16px 24px 24px 24px;
}
.chat-area {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  height: 100%;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: var(--shadow-md);
  border: 1px solid rgba(255, 255, 255, 0.8);
  overflow: hidden;
}

.chat-header {
  padding: 24px 32px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.6);
  background: rgba(255,255,255,0.4);
  z-index: 10;
}
.header-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.5px;
}
.header-subtitle {
  font-size: 13px;
  color: #64748b;
  margin-top: 6px;
  font-weight: 500;
}

/* -------------------------------------
   对话流 (Messages) & 动画
-------------------------------------- */
@keyframes slideUpFade {
  from { opacity: 0; transform: translateY(15px); }
  to { opacity: 1; transform: translateY(0); }
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
  scroll-behavior: smooth;
}
.messages-container::-webkit-scrollbar { width: 6px; }
.messages-container::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.2); border-radius: 6px; }

.message-wrapper {
  display: flex;
  margin-bottom: 32px;
  gap: 16px;
  max-width: 100%;
  animation: slideUpFade 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
.message-wrapper.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 40px;
  height: 40px;
  background: #ffffff;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
  border: 1px solid rgba(226, 232, 240, 0.8);
}
.message-wrapper.user .avatar {
  background: var(--primary-gradient);
  color: white;
  border: none;
}

.message-content {
  max-width: 82%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-bubble {
  padding: 16px 22px;
  border-radius: 16px;
  font-size: 15px;
  line-height: 1.7;
  position: relative;
  letter-spacing: 0.2px;
}

.message-wrapper.user .message-content {
  align-items: flex-end;
}

.user-bubble {
  background: var(--primary-gradient);
  color: white;
  border-top-right-radius: 4px;
  box-shadow: 0 8px 20px rgba(13, 148, 136, 0.2);
  word-break: break-word;
  white-space: pre-wrap;
  letter-spacing: normal;
  width: max-content;
  max-width: 100%;
}

.ai-bubble {
  background: #ffffff;
  color: #334155;
  border: 1px solid rgba(226,232,240, 0.6);
  border-top-left-radius: 4px;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.04);
}

.markdown-body p { margin-top: 0; margin-bottom: 0.8em; }
.markdown-body p:last-child { margin-bottom: 0; }
.markdown-body ul, .markdown-body ol { margin-top: 0.5em; margin-bottom: 0.5em; padding-left: 1.5em; }
.markdown-body strong { color: #0f172a; font-weight: 700; }

.welcome-bubble {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #e2e8f0;
}
.welcome-bubble h3 { margin-top: 0; color: var(--primary); font-weight: 700; }

.disclaimer {
  margin-top: 20px;
  padding: 14px 16px;
  background: #fff1f2;
  border-left: 4px solid var(--risk-high);
  border-radius: 8px;
  color: #be123c;
  font-size: 13px;
  display: flex;
  gap: 12px;
  align-items: flex-start;
  box-shadow: 0 2px 8px rgba(225, 29, 72, 0.05);
}
.disclaimer svg { flex-shrink: 0; margin-top: 2px; }

/* -------------------------------------
   实体“动态处方笺”分诊卡片 (Skeuomorphic Triage Card)
-------------------------------------- */
.triage-card {
  margin-top: 12px;
  background: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 25px rgba(0,0,0,0.06), 0 4px 10px rgba(0,0,0,0.03);
  position: relative;
  border: 1px solid #e2e8f0;
  /* 模拟纸张质感底纹 */
  background-image: radial-gradient(#cbd5e1 0.5px, transparent 0.5px);
  background-size: 16px 16px;
  background-color: #ffffff;
  background-position: 0 0, 8px 8px;
}
.triage-card::before {
  content: "⚕️ CLINICAL TRIAGE";
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-15deg);
  font-size: 40px;
  color: rgba(203, 213, 225, 0.15);
  font-weight: 900;
  white-space: nowrap;
  pointer-events: none;
}

.triage-card.risk-low { border-top: 4px solid var(--risk-low); }
.triage-card.risk-medium { border-top: 4px solid var(--risk-med); }
.triage-card.risk-high { border-top: 4px solid var(--risk-high); }

.triage-header {
  background: rgba(255,255,255,0.9);
  padding: 16px 20px;
  border-bottom: 1px dashed #cbd5e1;
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
  z-index: 2;
}
.triage-header h4 {
  margin: 0;
  color: #0f172a;
  font-size: 16px;
  font-weight: 700;
}

.triage-body {
  padding: 24px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: rgba(255,255,255,0.95);
  position: relative;
  z-index: 2;
}

.triage-row {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}
.triage-row.suggestion {
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}
.triage-label {
  color: #64748b;
  font-size: 13px;
  width: 100px;
  flex-shrink: 0;
  padding-top: 3px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.triage-value {
  color: #1e293b;
  font-size: 15px;
  margin: 0;
  font-weight: 500;
}
.triage-value.dept {
  font-weight: 700;
  color: var(--primary);
  font-size: 18px;
}

.risk-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 700;
  box-shadow: inset 0 0 0 1px rgba(0,0,0,0.1);
}
.pulse-dot {
  width: 6px;
  height: 6px;
  background: currentColor;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0% { transform: scale(0.95); opacity: 1; }
  50% { transform: scale(1.5); opacity: 0.5; }
  100% { transform: scale(0.95); opacity: 1; }
}

.risk-badge.risk-low { background: #ecfdf5; color: #047857; }
.risk-badge.risk-medium { background: #fffbeb; color: #b45309; }
.risk-badge.risk-high { background: #fef2f2; color: #b91c1c; }

/* -------------------------------------
   溯源抽屉 (Evidence Panel)
-------------------------------------- */
.evidence-panel {
  margin-top: 16px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}
.evidence-summary {
  padding: 12px 16px;
  font-size: 13px;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  user-select: none;
  background: #f8fafc;
  transition: all 0.2s;
  font-weight: 500;
}
.evidence-summary:hover { background: #f1f5f9; color: #0f172a; }
.evidence-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.evidence-item {
  font-size: 13.5px;
  color: #334155;
  padding: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}
.evidence-source {
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 8px;
  display: flex;
  justify-content: space-between;
}
.badge {
  background: #e0f2fe;
  color: #0369a1;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
.evidence-snippet {
  font-style: italic;
  color: #475569;
  line-height: 1.6;
}

/* -------------------------------------
   输入区 (Input Area)
-------------------------------------- */
.input-area-wrapper {
  padding: 24px 32px;
  background: rgba(255,255,255,0.8);
  border-top: 1px solid rgba(226, 232, 240, 0.6);
}

.input-container {
  display: flex;
  gap: 14px;
  background: #ffffff;
  padding: 10px 10px 10px 24px;
  border: 1px solid #cbd5e1;
  border-radius: 9999px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 10px rgba(0,0,0,0.03);
}
.input-container:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 4px rgba(13, 148, 136, 0.15), 0 4px 15px rgba(0,0,0,0.05);
}

.chat-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 16px;
  color: #0f172a;
  outline: none;
}
.chat-input::placeholder { color: #94a3b8; font-weight: 400; }

.send-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--primary-gradient);
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3);
}
.send-btn:hover:not(:disabled) {
  transform: scale(1.08);
  box-shadow: 0 6px 16px rgba(13, 148, 136, 0.4);
}
.send-btn:disabled {
  background: #cbd5e1;
  box-shadow: none;
  cursor: not-allowed;
}

.input-footer {
  text-align: center;
  font-size: 12.5px;
  color: #94a3b8;
  margin-top: 16px;
  font-weight: 500;
}
</style>

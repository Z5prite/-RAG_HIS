<script setup>
import { ref, onMounted, nextTick, reactive } from 'vue'
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

const triggerQuickQuery = (text) => {
  inputText.value = text
  sendMessage()
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
  
  const targetMsg = reactive({
    role: 'assistant',
    content: '',
    metadata: {}
  })
  messages.value.push(targetMsg)
  scrollToBottom()

  try {
    const isDev = import.meta.env.DEV
    const apiBase = isDev ? 'http://127.0.0.1:8012' : ''
    console.log(`[RAG Debug] Fetching URL: ${apiBase}/api/chat | isDev: ${isDev}`)
    const res = await fetch(`${apiBase}/api/chat`, {
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
  <div v-else-if="currentUserRole === 'admin'" class="app-container admin-mode">
    <AdminPanel @close="handleLogout" />
  </div>

  <!-- 普通医生/患者接诊台 -->
  <div v-else class="app-container">
    <!-- 侧边栏: Glassmorphism Clinical Menu -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="brand">
          <div class="brand-icon-wrapper">
            <span class="brand-icon">⚕️</span>
          </div>
          <div class="brand-text">
            <h2>HIS RAG</h2>
            <span class="brand-badge">Clinical Engine</span>
          </div>
        </div>
        <button class="new-chat-btn" @click="createNewChat">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          开始新接诊 / NEW
        </button>
      </div>
      
      <div class="session-list">
        <div class="session-group-title">历史接诊记录 / ARCHIVE</div>
        <div 
          v-for="s in sessions" 
          :key="s.session_id"
          class="session-item"
          :class="{ active: s.session_id === activeSessionId }"
          @click="selectSession(s.session_id)"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="session-icon"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
          <span class="session-title">{{ s.title || '无标题接诊' }}</span>
          <button class="session-delete-btn" @click="(e) => deleteSession(s.session_id, e)" title="删除记录">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
          </button>
        </div>
      </div>
      
      <div class="sidebar-footer">
        <button class="logout-btn" @click="handleLogout">
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
          退出系统 ({{ currentUserRole === 'user' ? '医生' : currentUserRole }})
        </button>
      </div>
    </aside>

    <!-- 主工作区 -->
    <main class="main-content">
      <div class="chat-area">
        <header class="chat-header">
          <div class="header-left">
            <h1 class="header-title">智能辅助诊疗工作台</h1>
            <div class="header-meta">
              <span class="system-status-indicator">
                <span class="indicator-dot online"></span>
                RAG 检索增强引擎就绪
              </span>
              <span class="separator">|</span>
              <span class="session-id-display" v-if="activeSessionId">
                会话编码: <code>{{ activeSessionId.slice(0, 8) }}...</code>
              </span>
              <span class="session-id-display" v-else>
                状态: <code>空闲新接诊</code>
              </span>
            </div>
          </div>
          <div class="header-right">
            <span class="terminal-badge">RAG CORE v1.0</span>
          </div>
        </header>
        
        <div class="messages-container" ref="messagesContainer">
          <!-- Welcome Dashboard -->
          <div v-if="messages.length === 0" class="welcome-container">
            <div class="welcome-banner">
              <div class="banner-icon">⚕️</div>
              <h2>您好！我是您的智能数字医疗助理</h2>
              <p>系统已连接社区医院本地诊疗指南知识库，可为您提供严谨的分诊建议与医学科普。</p>
            </div>

            <div class="quick-start-section">
              <div class="section-title-line">
                <span>常见病症自诊输入示范 / COMMON SYMPTOMS</span>
              </div>
              <div class="quick-queries-grid">
                <div class="quick-query-card" @click="triggerQuickQuery('最近总是胸闷气短，尤其是爬楼梯的时候，偶尔有心慌的感觉。')">
                  <div class="qq-header">
                    <span class="qq-icon">🫀</span>
                    <h4>胸闷心慌气短</h4>
                  </div>
                  <p class="qq-desc">适用于评估潜在心脑血管征兆，协助进行紧急分诊排查。</p>
                  <div class="qq-action">一键模拟输入 →</div>
                </div>

                <div class="quick-query-card" @click="triggerQuickQuery('三岁的小孩昨晚开始发烧，量了下是38.6度，稍微有一点点咳嗽，但是精神状态还可以，需要马上去挂急诊吗？')">
                  <div class="qq-header">
                    <span class="qq-icon">👶</span>
                    <h4>小儿发热咳嗽</h4>
                  </div>
                  <p class="qq-desc">指导儿科轻症与重症的界限判断，以及居家基础护理常识。</p>
                  <div class="qq-action">一键模拟输入 →</div>
                </div>

                <div class="quick-query-card" @click="triggerQuickQuery('体检报告查出来空腹血糖7.3，日常生活有什么需要注意的吗？需要马上吃降糖药吗？')">
                  <div class="qq-header">
                    <span class="qq-icon">🍬</span>
                    <h4>体检血糖偏高</h4>
                  </div>
                  <p class="qq-desc">解答常见代谢类慢病指标咨询，提供权威膳食和作息医嘱建议。</p>
                  <div class="qq-action">一键模拟输入 →</div>
                </div>

                <div class="quick-query-card" @click="triggerQuickQuery('突然剧烈头痛，像针扎一样，伴有一阵一阵的恶心呕吐，右边胳膊感觉有点抬不起来，发麻。')">
                  <div class="qq-header">
                    <span class="qq-icon">🚨</span>
                    <h4>突发偏瘫式头痛</h4>
                  </div>
                  <p class="qq-desc">模拟高危突发症状拦截，触发急诊红色警报与生命通道指引。</p>
                  <div class="qq-action">一键模拟输入 →</div>
                </div>
              </div>
            </div>

            <div class="welcome-disclaimer">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="disc-icon"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
              <div class="disc-text">
                <strong>免责声明：</strong>AI 决策系统给出的任何诊断建议及推荐科室仅供临床参考，不能代替执业医师的现场诊断与处方。如有严重不适，请立刻拨打 120 紧急就医。
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
                <div v-if="msg.metadata && msg.metadata.department && msg.metadata.department !== '无需就医'" class="triage-ticket" :class="getRiskClass(msg.metadata.risk)">
                  <div class="ticket-sawtooth"></div>
                  <div class="ticket-header">
                    <span class="ticket-badge">CLINICAL TRIAGE TICKET</span>
                    <h4>智能就诊分诊单</h4>
                    <div class="ticket-barcode">||| | |||| | ||</div>
                  </div>
                  <div class="ticket-body">
                    <div class="ticket-meta">
                      <span>凭证编号: {{ activeSessionId ? activeSessionId.slice(0, 10).toUpperCase() : 'TEMP-PRESCRIPTION' }}</span>
                      <span>等级: 临床分类管理</span>
                    </div>
                    
                    <div class="ticket-grid">
                      <div class="ticket-cell">
                        <span class="cell-label">推荐就诊科室 / RECOMMENDED DEPT</span>
                        <span class="cell-value dept-value">{{ msg.metadata.department }}</span>
                      </div>
                      <div class="ticket-cell">
                        <span class="cell-label">评估分级 / RISK LEVEL</span>
                        <div class="risk-badge-ticket" :class="getRiskClass(msg.metadata.risk)">
                          <span class="pulse-dot" v-if="msg.metadata.risk?.includes('急诊') || msg.metadata.risk?.includes('高')"></span>
                          {{ msg.metadata.risk }}
                        </div>
                      </div>
                    </div>
                    
                    <div class="ticket-divider-dash"></div>
                    
                    <div class="ticket-suggestion" v-if="msg.metadata.suggestion">
                      <span class="cell-label">医生指导建议 / CLINICAL SUGGESTION</span>
                      <p class="suggestion-p">{{ msg.metadata.suggestion }}</p>
                    </div>
                  </div>
                  <div class="ticket-footer">
                    <span>* 本建议书仅用于分诊指导，不代表医师处方诊断结论 *</span>
                  </div>
                </div>

                <!-- 溯源面板 -->
                <details v-if="msg.metadata && msg.metadata.evidence && msg.metadata.evidence.length > 0" class="evidence-panel">
                  <summary class="evidence-summary">
                    <svg class="summary-icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>
                    <span>知识库溯源文献 ({{ msg.metadata.evidence.length }} 条)</span>
                    <span class="arrow-icon">▾</span>
                  </summary>
                  <div class="evidence-content">
                    <div v-for="(ev, i) in msg.metadata.evidence" :key="i" class="evidence-item">
                      <div class="evidence-item-header">
                        <div class="evidence-source">
                          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="file-icon-svg"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                          <span class="source-title">{{ ev.source }}</span>
                        </div>
                        <span class="source-badge">{{ ev.section }}</span>
                      </div>
                      <div class="evidence-snippet">
                        <span class="quote-symbol">“</span>
                        {{ ev.snippet }}
                        <span class="quote-symbol">”</span>
                      </div>
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
              placeholder="请输入您的主诉症状，例如：最近总是心慌胸闷，偶有头晕..." 
              :disabled="isGenerating"
            />
            <button class="send-btn" @click="sendMessage" :disabled="isGenerating || !inputText.trim()">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
            </button>
          </div>
          <div class="input-footer">大模型自动检索院内医学规范提供答复，不可替代专业现场临床诊断。</div>
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
   全局重置与设计系统 tokens
-------------------------------------- */
:root {
  --primary: #0d9488;
  --primary-hover: #0f766e;
  --primary-gradient: linear-gradient(135deg, #0d9488, #0f766e);
  --bg-main: #f1f5f9;
  --bg-sidebar: rgba(255, 255, 255, 0.7);
  --text-main: #0f172a;
  --text-muted: #475569;
  --text-light: #64748b;
  --risk-low: #059669;
  --risk-med: #d97706;
  --risk-high: #e11d48;
  
  --shadow-sm: 0 1px 3px 0 rgba(15, 23, 42, 0.03), 0 1px 2px -1px rgba(15, 23, 42, 0.02);
  --shadow-md: 0 4px 6px -1px rgba(15, 23, 42, 0.05), 0 2px 4px -2px rgba(15, 23, 42, 0.03);
  --shadow-lg: 0 10px 25px -5px rgba(15, 23, 42, 0.05), 0 8px 10px -6px rgba(15, 23, 42, 0.03);
}

body {
  margin: 0;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  color: var(--text-main);
  background-color: var(--bg-main);
  height: 100vh;
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  background-color: #f1f5f9;
}

.app-container.admin-mode {
  background: #f8fafc;
}

/* -------------------------------------
   侧边栏 (Clinical Glassmorphism Sidebar)
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
  border-right: 1px solid rgba(226, 232, 240, 0.8);
  z-index: 20;
}

.sidebar-header {
  padding: 24px 20px 16px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.brand-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  background: var(--primary-gradient);
  border-radius: 10px;
  box-shadow: 0 4px 10px rgba(13, 148, 136, 0.2);
}

.brand-icon {
  font-size: 20px;
  color: white;
}

.brand-text h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #0f172a;
}

.brand-badge {
  font-size: 10px;
  color: var(--primary);
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-weight: 700;
}

.new-chat-btn {
  width: 100%;
  padding: 12px 16px;
  background: var(--primary-gradient);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s ease-out;
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.15);
}

.new-chat-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(13, 148, 136, 0.25);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 16px;
}

.session-list::-webkit-scrollbar {
  width: 4px;
}
.session-list::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
  border-radius: 4px;
}

.session-group-title {
  font-size: 11px;
  font-family: ui-monospace, SFMono-Regular, monospace;
  color: #94a3b8;
  margin: 16px 8px 8px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.session-item {
  padding: 10px 12px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 13.5px;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.2s;
  background: transparent;
  border: 1px solid transparent;
}

.session-item:hover {
  background: rgba(255, 255, 255, 0.8);
  border-color: rgba(255, 255, 255, 1);
  color: var(--text-main);
}

.session-item.active {
  background: #ffffff;
  color: #0d9488;
  font-weight: 600;
  border-color: rgba(226, 232, 240, 0.8);
  box-shadow: var(--shadow-sm);
}

.session-icon {
  opacity: 0.5;
  color: #94a3b8;
  flex-shrink: 0;
}

.session-item.active .session-icon {
  opacity: 1;
  color: var(--primary);
}

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
  color: #e11d48;
  background: rgba(225, 29, 72, 0.08);
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(226, 232, 240, 0.8);
}

.logout-btn {
  width: 100%;
  padding: 10px;
  background: transparent;
  color: #e11d48;
  border: 1px dashed rgba(225, 29, 72, 0.3);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: #fef2f2;
  border-color: #e11d48;
}

/* -------------------------------------
   主工作区 & 顶栏
-------------------------------------- */
.main-content {
  flex: 1;
  display: flex;
  position: relative;
  padding: 16px 20px 20px 20px;
}

.chat-area {
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  height: 100%;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: var(--shadow-lg);
  border: 1px solid rgba(255, 255, 255, 0.9);
  overflow: hidden;
}

.chat-header {
  padding: 20px 28px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.8);
  background: rgba(255, 255, 255, 0.4);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-size: 17px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.01em;
  margin: 0;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
}

.system-status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
}

.indicator-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.indicator-dot.online {
  background-color: #0d9488;
  box-shadow: 0 0 8px rgba(13, 148, 136, 0.5);
}

.separator {
  color: #e2e8f0;
  font-size: 12px;
}

.session-id-display {
  font-size: 12px;
  color: var(--text-light);
}

.session-id-display code {
  font-family: ui-monospace, SFMono-Regular, monospace;
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  color: var(--text-muted);
}

.terminal-badge {
  font-size: 10px;
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-weight: 700;
  color: #64748b;
  border: 1px solid #e2e8f0;
  padding: 3px 8px;
  border-radius: 6px;
  background: #f8fafc;
}

/* -------------------------------------
   欢迎大屏 (Welcome Grid Dashboard)
-------------------------------------- */
.welcome-container {
  display: flex;
  flex-direction: column;
  gap: 32px;
  padding: 12px 0 24px 0;
  max-width: 880px;
  margin: 0 auto;
}

.welcome-banner {
  text-align: center;
  margin-top: 10px;
}

.banner-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

.welcome-banner h2 {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 8px 0;
  letter-spacing: -0.02em;
}

.welcome-banner p {
  font-size: 14.5px;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.5;
}

.section-title-line {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.section-title-line span {
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  letter-spacing: 0.1em;
  background: transparent;
  padding: 0 16px;
}

.quick-queries-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.quick-query-card {
  background: #ffffff;
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.01);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.quick-query-card:hover {
  transform: translateY(-2px);
  border-color: rgba(13, 148, 136, 0.3);
  box-shadow: var(--shadow-lg);
  background: rgba(13, 148, 136, 0.01);
}

.qq-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.qq-icon {
  font-size: 18px;
}

.qq-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.qq-desc {
  font-size: 12.5px;
  color: var(--text-light);
  line-height: 1.55;
  margin: 0 0 12px 0;
  flex: 1;
}

.qq-action {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--primary);
  transition: color 0.2s;
  display: flex;
  align-items: center;
}

.quick-query-card:hover .qq-action {
  color: var(--primary-hover);
}

.welcome-disclaimer {
  display: flex;
  gap: 12px;
  background: #fff1f2;
  border: 1px solid #ffe4e6;
  border-radius: 10px;
  padding: 14px 18px;
  align-items: flex-start;
}

.disc-icon {
  color: var(--risk-high);
  flex-shrink: 0;
  margin-top: 2px;
}

.disc-text {
  font-size: 13px;
  color: #be123c;
  line-height: 1.5;
}

/* -------------------------------------
   对话流消息气泡 (Modern Chat Bubbles)
-------------------------------------- */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px;
}

.message-wrapper {
  display: flex;
  margin-bottom: 24px;
  gap: 14px;
  max-width: 100%;
}

.message-wrapper.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  background: #ffffff;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.message-content {
  max-width: 85%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-wrapper.user .message-content {
  align-items: flex-end;
}

.user-bubble {
  padding: 12px 18px;
  border-radius: 14px;
  font-size: 14.5px;
  line-height: 1.6;
  background: var(--primary-gradient);
  color: white;
  border-top-right-radius: 4px;
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.15);
  word-break: break-word;
  white-space: pre-wrap;
}

.ai-bubble {
  padding: 16px 20px;
  border-radius: 14px;
  font-size: 14.5px;
  line-height: 1.65;
  background: #ffffff;
  color: #1e293b;
  border: 1px solid rgba(226, 232, 240, 0.7);
  border-top-left-radius: 4px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
}

/* Markdown typography settings */
.markdown-body {
  color: #334155;
}
.markdown-body p {
  margin-top: 0;
  margin-bottom: 8px;
}
.markdown-body p:last-child {
  margin-bottom: 0;
}
.markdown-body ul, .markdown-body ol {
  margin-top: 4px;
  margin-bottom: 8px;
  padding-left: 20px;
}
.markdown-body li {
  margin-bottom: 4px;
}
.markdown-body strong {
  color: #0f172a;
  font-weight: 700;
}

/* -------------------------------------
   印刷热敏纸凭证卡 (Skeuomorphic Prescription Ticket)
-------------------------------------- */
.triage-ticket {
  margin-top: 14px;
  background-color: #fafaf9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;
  background-image: 
    linear-gradient(#f1f5f9 1px, transparent 1px),
    linear-gradient(90deg, #f1f5f9 1px, transparent 1px);
  background-size: 16px 16px;
}

.ticket-sawtooth {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background-image: linear-gradient(135deg, transparent 66%, #cbd5e1 66%), linear-gradient(225deg, transparent 66%, #cbd5e1 66%);
  background-size: 8px 12px;
  background-repeat: repeat-x;
  background-position: 0 0;
  transform: translateY(-2px);
}

.triage-ticket.risk-low { border-top: 3px solid var(--risk-low); }
.triage-ticket.risk-medium { border-top: 3px solid var(--risk-med); }
.triage-ticket.risk-high { border-top: 3px solid var(--risk-high); }

.ticket-header {
  padding: 16px 20px 10px 20px;
  border-bottom: 1px dashed #cbd5e1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ticket-badge {
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.1em;
  padding: 2px 6px;
  background: #f1f5f9;
  border-radius: 4px;
  color: #64748b;
}

.ticket-header h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.ticket-barcode {
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-size: 11px;
  color: #94a3b8;
  letter-spacing: 1px;
}

.ticket-body {
  padding: 16px 20px;
}

.ticket-meta {
  display: flex;
  justify-content: space-between;
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-size: 11px;
  color: #94a3b8;
  margin-bottom: 12px;
}

.ticket-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
  margin-bottom: 14px;
}

.ticket-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cell-label {
  font-size: 10px;
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-weight: 700;
  color: #64748b;
  letter-spacing: 0.05em;
}

.cell-value {
  font-size: 14px;
  color: #0f172a;
  font-weight: 600;
}

.cell-value.dept-value {
  font-size: 18px;
  color: var(--primary);
  font-weight: 700;
}

.risk-badge-ticket {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 6px;
  width: max-content;
}

.risk-badge-ticket.risk-low { background-color: #ecfdf5; color: #047857; }
.risk-badge-ticket.risk-medium { background-color: #fffbeb; color: #b45309; }
.risk-badge-ticket.risk-high { background-color: #fef2f2; color: #b91c1c; }

.ticket-divider-dash {
  height: 1px;
  border-top: 1px dashed #e2e8f0;
  margin: 12px 0;
}

.ticket-suggestion {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.suggestion-p {
  font-size: 13px;
  line-height: 1.55;
  color: #334155;
  margin: 0;
  background: rgba(255,255,255,0.7);
  padding: 10px 12px;
  border-radius: 6px;
  border: 1px solid rgba(226,232,240,0.5);
}

.ticket-footer {
  padding: 8px 20px 12px 20px;
  text-align: center;
  border-top: 1px dashed #cbd5e1;
}

.ticket-footer span {
  font-size: 10px;
  color: #94a3b8;
  font-weight: 500;
}

/* -------------------------------------
   证据来源抽屉面板 (Evidence/Citations Drawer)
-------------------------------------- */
.evidence-panel {
  margin-top: 14px;
  background: #ffffff;
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.evidence-summary {
  padding: 10px 14px;
  font-size: 12.5px;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  user-select: none;
  background: #f8fafc;
  transition: all 0.2s;
  font-weight: 600;
}

.evidence-summary:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.evidence-summary .arrow-icon {
  margin-left: auto;
  font-size: 11px;
  color: #94a3b8;
  transition: transform 0.2s;
}

.evidence-panel[open] .arrow-icon {
  transform: rotate(180deg);
}

.summary-icon {
  color: #94a3b8;
}

.evidence-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #ffffff;
  border-top: 1px solid rgba(226, 232, 240, 0.8);
}

.evidence-item {
  background: #f8fafc;
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 8px;
  padding: 12px;
}

.evidence-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.evidence-source {
  display: flex;
  align-items: center;
  gap: 6px;
}

.file-icon-svg {
  color: var(--primary);
  flex-shrink: 0;
}

.source-title {
  font-size: 12px;
  font-weight: 700;
  color: #334155;
  font-family: ui-monospace, SFMono-Regular, monospace;
}

.source-badge {
  background: #e0f2fe;
  color: #0369a1;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
}

.evidence-snippet {
  font-size: 12.5px;
  color: #475569;
  line-height: 1.5;
  font-style: italic;
  padding-left: 8px;
  border-left: 2px solid #cbd5e1;
}

.quote-symbol {
  color: #cbd5e1;
  font-weight: 700;
  font-size: 14px;
}

/* -------------------------------------
   底栏输入区域 (Rounded Pill Input)
-------------------------------------- */
.input-area-wrapper {
  padding: 20px 28px 24px 28px;
  background: rgba(255, 255, 255, 0.8);
  border-top: 1px solid rgba(226, 232, 240, 0.8);
}

.input-container {
  display: flex;
  gap: 12px;
  background: #ffffff;
  padding: 6px 6px 6px 20px;
  border: 1px solid #cbd5e1;
  border-radius: 9999px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-sm);
  align-items: center;
}

.input-container:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.12), var(--shadow-md);
}

.chat-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 15px;
  color: #0f172a;
  outline: none;
  padding: 6px 0;
}

.chat-input::placeholder {
  color: #94a3b8;
}

.send-btn {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--primary-gradient);
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease-out;
  box-shadow: 0 2px 6px rgba(13, 148, 136, 0.2);
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.06);
  box-shadow: 0 4px 10px rgba(13, 148, 136, 0.3);
}

.send-btn:disabled {
  background: #cbd5e1;
  box-shadow: none;
  cursor: not-allowed;
}

.input-footer {
  text-align: center;
  font-size: 12px;
  color: #94a3b8;
  margin-top: 12px;
  font-weight: 500;
}

/* Base animations */
@keyframes slideUpFade {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.welcome-container, .message-wrapper {
  animation: slideUpFade 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
</style>

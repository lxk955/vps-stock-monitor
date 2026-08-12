<template>
  <div
    v-if="visible"
    @click.self="close"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs"
  >
    <div class="relative w-full max-w-2xl bg-card border border-border rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 max-h-[90vh] flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-border/80 bg-secondary/30 shrink-0">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center">
            <Settings class="w-4 h-4" />
          </div>
          <div>
            <h3 class="font-bold text-sm text-foreground">管理后台与系统设置</h3>
            <p class="text-[11px] text-muted-foreground">配置 SMTP 邮件、各大厂商 AFF 推广返利、监控冷却与爬虫</p>
          </div>
        </div>

        <button @click="close" class="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors">
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Password Lock Screen if not authenticated -->
      <div v-if="!isAuthenticated" class="p-8 text-center space-y-4 my-auto">
        <Lock class="w-10 h-10 mx-auto text-muted-foreground opacity-60" />
        <div class="space-y-1">
          <h4 class="font-bold text-sm text-foreground">管理员身份验证</h4>
          <p class="text-xs text-muted-foreground">请输入后台管理员密码以访问高级设置 (默认: admin123456)</p>
        </div>

        <form @submit.prevent="verifyPassword" class="max-w-xs mx-auto space-y-3">
          <input
            type="password"
            v-model="passwordInput"
            placeholder="管理员密码"
            class="w-full px-3 py-2 text-xs rounded-lg bg-background border border-border focus:outline-none focus:border-primary font-mono text-center"
          />
          <button
            type="submit"
            :disabled="authChecking || !passwordInput"
            class="w-full py-2 bg-primary text-primary-foreground font-bold rounded-lg text-xs hover:opacity-90 disabled:opacity-50 transition-all flex items-center justify-center gap-1.5"
          >
            <Loader2 v-if="authChecking" class="w-3.5 h-3.5 animate-spin" />
            <span>验证并解锁</span>
          </button>
        </form>
      </div>

      <!-- Main Authenticated Tabs -->
      <template v-else>
        <div class="flex items-center border-b border-border/60 px-5 bg-secondary/10 shrink-0 text-xs font-semibold overflow-x-auto justify-between">
          <div class="flex items-center">
            <button
              @click="tab = 'smtp'"
              class="py-2.5 px-3 border-b-2 transition-all whitespace-nowrap"
              :class="tab === 'smtp' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'"
            >
              📧 SMTP 邮件
            </button>
            <button
              @click="tab = 'aff'"
              class="py-2.5 px-3 border-b-2 transition-all whitespace-nowrap flex items-center gap-1"
              :class="tab === 'aff' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'"
            >
              <span>💰 AFF 推广返利</span>
              <span class="px-1 py-0.2 rounded bg-amber-500/10 text-amber-600 text-[9px] font-bold">New</span>
            </button>
            <button
              @click="tab = 'crawler'"
              class="py-2.5 px-3 border-b-2 transition-all whitespace-nowrap"
              :class="tab === 'crawler' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'"
            >
              ⚙️ 监控与冷却
            </button>
            <button
              @click="tab = 'logs'"
              class="py-2.5 px-3 border-b-2 transition-all whitespace-nowrap"
              :class="tab === 'logs' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'"
            >
              📜 发信审计日志
            </button>
          </div>

          <button
            @click="logout"
            class="text-[11px] text-muted-foreground hover:text-destructive transition-colors py-1 px-2 rounded whitespace-nowrap"
          >
            退出登录
          </button>
        </div>

        <div class="p-5 overflow-y-auto space-y-4 flex-1 text-xs">
          <!-- TAB 1: SMTP Settings -->
          <div v-if="tab === 'smtp'" class="space-y-4">
            <!-- Preset Quick Selectors -->
            <div class="p-3 rounded-xl bg-secondary/40 border border-border/60 space-y-2">
              <div class="font-semibold text-foreground flex items-center justify-between">
                <span>⚡ 常用发信邮箱一键预设</span>
                <span class="text-[10px] text-muted-foreground">自动填充服务器与端口</span>
              </div>
              <div class="flex flex-wrap gap-1.5">
                <button
                  type="button"
                  @click="applyPreset('qq')"
                  class="px-2.5 py-1 rounded-md bg-card border border-border hover:border-primary text-[11px] font-medium transition-colors"
                >
                  QQ 邮箱 (smtp.qq.com:465)
                </button>
                <button
                  type="button"
                  @click="applyPreset('163')"
                  class="px-2.5 py-1 rounded-md bg-card border border-border hover:border-primary text-[11px] font-medium transition-colors"
                >
                  163 邮箱 (smtp.163.com:465)
                </button>
                <button
                  type="button"
                  @click="applyPreset('gmail')"
                  class="px-2.5 py-1 rounded-md bg-card border border-border hover:border-primary text-[11px] font-medium transition-colors"
                >
                  Gmail (smtp.gmail.com:587)
                </button>
                <button
                  type="button"
                  @click="applyPreset('aliyun')"
                  class="px-2.5 py-1 rounded-md bg-card border border-border hover:border-primary text-[11px] font-medium transition-colors"
                >
                  阿里云企业邮 (smtp.qiye.aliyun.com:465)
                </button>
              </div>
            </div>

            <!-- SMTP Form -->
            <form @submit.prevent="saveSmtpSettings" class="space-y-3">
              <div class="grid grid-cols-2 gap-3">
                <div class="space-y-1">
                  <label class="font-semibold text-foreground">SMTP 服务器地址</label>
                  <input
                    type="text"
                    required
                    v-model="smtpForm.smtp_host"
                    placeholder="如 smtp.qq.com"
                    class="w-full px-3 py-1.5 rounded-lg bg-background border border-border font-mono text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div class="space-y-1">
                  <label class="font-semibold text-foreground">SMTP 端口</label>
                  <input
                    type="number"
                    required
                    v-model.number="smtpForm.smtp_port"
                    placeholder="465 或 587"
                    class="w-full px-3 py-1.5 rounded-lg bg-background border border-border font-mono text-xs focus:outline-none focus:border-primary"
                  />
                </div>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div class="space-y-1">
                  <label class="font-semibold text-foreground">发件邮箱账号 (User)</label>
                  <input
                    type="email"
                    required
                    v-model="smtpForm.smtp_user"
                    placeholder="your-email@qq.com"
                    class="w-full px-3 py-1.5 rounded-lg bg-background border border-border font-mono text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div class="space-y-1">
                  <label class="font-semibold text-foreground">
                    邮箱授权码 / 密码
                    <span v-if="smtpForm.smtp_pass_configured" class="text-emerald-500 text-[10px] font-normal">(已配置)</span>
                  </label>
                  <input
                    type="password"
                    v-model="smtpForm.smtp_pass"
                    placeholder="留空表示不修改原密码"
                    class="w-full px-3 py-1.5 rounded-lg bg-background border border-border font-mono text-xs focus:outline-none focus:border-primary"
                  />
                </div>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div class="space-y-1">
                  <label class="font-semibold text-foreground">发件人显示名称</label>
                  <input
                    type="text"
                    v-model="smtpForm.smtp_from_name"
                    placeholder="VPS 实时库存与降价监控"
                    class="w-full px-3 py-1.5 rounded-lg bg-background border border-border text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div class="space-y-1">
                  <label class="font-semibold text-foreground">前端访问网址 (Site URL)</label>
                  <input
                    type="text"
                    v-model="smtpForm.site_url"
                    placeholder="http://localhost:5173"
                    class="w-full px-3 py-1.5 rounded-lg bg-background border border-border font-mono text-xs focus:outline-none focus:border-primary"
                  />
                </div>
              </div>

              <div class="flex items-center gap-4 pt-1">
                <label class="flex items-center gap-1.5 cursor-pointer">
                  <input type="checkbox" v-model="smtpForm.smtp_ssl" class="rounded border-border text-primary focus:ring-primary" />
                  <span>启用 SSL 加密 (端口 465 推荐)</span>
                </label>
                <label class="flex items-center gap-1.5 cursor-pointer">
                  <input type="checkbox" v-model="smtpForm.smtp_tls" class="rounded border-border text-primary focus:ring-primary" />
                  <span>启用 STARTTLS (端口 587 推荐)</span>
                </label>
              </div>

              <div class="flex items-center justify-between pt-3 border-t border-border/60">
                <button
                  type="submit"
                  :disabled="saving"
                  class="py-2 px-5 bg-primary text-primary-foreground font-bold rounded-lg text-xs hover:opacity-90 disabled:opacity-50 transition-all shadow-xs"
                >
                  {{ saving ? '保存中...' : '保存 SMTP 设置' }}
                </button>

                <!-- Test Email Trigger -->
                <div class="flex items-center gap-1.5">
                  <input
                    type="email"
                    v-model="testEmailInput"
                    placeholder="测试收件邮箱"
                    class="w-44 px-2.5 py-1.5 text-xs rounded-lg bg-background border border-border font-mono focus:outline-none focus:border-primary"
                  />
                  <button
                    type="button"
                    @click="sendTestEmail"
                    :disabled="testingEmail || !testEmailInput"
                    class="py-1.5 px-3 bg-secondary hover:bg-secondary/80 text-foreground border border-border rounded-lg text-xs font-semibold disabled:opacity-50 transition-colors flex items-center gap-1 shrink-0"
                  >
                    <Loader2 v-if="testingEmail" class="w-3.5 h-3.5 animate-spin" />
                    <span>{{ testingEmail ? '发送中...' : '发送测试' }}</span>
                  </button>
                </div>
              </div>

              <!-- Inline Test Email Feedback Banner -->
              <div
                v-if="testResult"
                class="p-3 rounded-xl border text-xs flex items-start gap-2 animate-in fade-in transition-all"
                :class="testResult.success ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30' : 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30'"
              >
                <span class="text-base shrink-0">{{ testResult.success ? '🎉' : '❌' }}</span>
                <div class="space-y-0.5">
                  <div class="font-bold">{{ testResult.success ? '测试发信成功' : '发信失败原因' }}</div>
                  <div class="text-[11px] leading-relaxed break-all opacity-90">{{ testResult.message }}</div>
                </div>
              </div>
            </form>
          </div>

          <!-- TAB 2: AFF Referral Settings (New Feature) -->
          <div v-else-if="tab === 'aff'" class="space-y-4">
            <div class="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-900 dark:text-amber-200 space-y-1">
              <div class="font-bold flex items-center gap-1">
                <span>💰 全局厂商 AFF 推广码自动注入引擎</span>
              </div>
              <p class="text-[11px] leading-relaxed opacity-90">
                在此填入你在各大 VPS 厂商的推广码/推荐 ID。系统会自动为全站对应厂商的<strong>所有产品购买按钮</strong>以及<strong>发出的邮件直达链接</strong>拼接上你的 AFF 返利参数，无需手动修改每个产品！
              </p>
            </div>

            <form @submit.prevent="saveAffSettings" class="space-y-4">
              <div class="grid grid-cols-2 gap-3">
                <div class="space-y-1">
                  <label class="font-semibold text-foreground">搬瓦工 BandwagonHost (aff=)</label>
                  <input
                    type="text"
                    v-model="affForm.aff_bwh"
                    placeholder="如 12345"
                    class="w-full px-3 py-1.5 rounded-lg bg-background border border-border font-mono text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div class="space-y-1">
                  <label class="font-semibold text-foreground">RackNerd (aff=)</label>
                  <input
                    type="text"
                    v-model="affForm.aff_racknerd"
                    placeholder="如 67890"
                    class="w-full px-3 py-1.5 rounded-lg bg-background border border-border font-mono text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div class="space-y-1">
                  <label class="font-semibold text-foreground">DMIT (aff=)</label>
                  <input
                    type="text"
                    v-model="affForm.aff_dmit"
                    placeholder="如 8888"
                    class="w-full px-3 py-1.5 rounded-lg bg-background border border-border font-mono text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div class="space-y-1">
                  <label class="font-semibold text-foreground">ClawCloud (aff=)</label>
                  <input
                    type="text"
                    v-model="affForm.aff_clawcloud"
                    placeholder="如 your_claw_id"
                    class="w-full px-3 py-1.5 rounded-lg bg-background border border-border font-mono text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div class="space-y-1">
                  <label class="font-semibold text-foreground">V.PS (xTom) (aff=)</label>
                  <input
                    type="text"
                    v-model="affForm.aff_vps"
                    placeholder="如 1122"
                    class="w-full px-3 py-1.5 rounded-lg bg-background border border-border font-mono text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div class="space-y-1">
                  <label class="font-semibold text-foreground">斯巴达 SpartanHost (aff=)</label>
                  <input
                    type="text"
                    v-model="affForm.aff_spartan"
                    placeholder="如 3344"
                    class="w-full px-3 py-1.5 rounded-lg bg-background border border-border font-mono text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div class="space-y-1">
                  <label class="font-semibold text-foreground">BuyVM (Frantech) (aff=)</label>
                  <input
                    type="text"
                    v-model="affForm.aff_buyvm"
                    placeholder="如 5566"
                    class="w-full px-3 py-1.5 rounded-lg bg-background border border-border font-mono text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div class="space-y-1">
                  <label class="font-semibold text-foreground">Netcup (ref=)</label>
                  <input
                    type="text"
                    v-model="affForm.aff_netcup"
                    placeholder="如 netcup_ref_id"
                    class="w-full px-3 py-1.5 rounded-lg bg-background border border-border font-mono text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div class="space-y-1">
                  <label class="font-semibold text-foreground">AkileCloud (aff_sub=)</label>
                  <input
                    type="text"
                    v-model="affForm.aff_akile"
                    placeholder="如 akile_id"
                    class="w-full px-3 py-1.5 rounded-lg bg-background border border-border font-mono text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div class="space-y-1">
                  <label class="font-semibold text-foreground">WikiHost 微基 (aff=)</label>
                  <input
                    type="text"
                    v-model="affForm.aff_wikihost"
                    placeholder="如 wikihost_id"
                    class="w-full px-3 py-1.5 rounded-lg bg-background border border-border font-mono text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div class="space-y-1">
                  <label class="font-semibold text-foreground">Kurun 库润 (aff=)</label>
                  <input
                    type="text"
                    v-model="affForm.aff_kurun"
                    placeholder="如 kurun_id"
                    class="w-full px-3 py-1.5 rounded-lg bg-background border border-border font-mono text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div class="space-y-1">
                  <label class="font-semibold text-foreground">CloudCone (ref=)</label>
                  <input
                    type="text"
                    v-model="affForm.aff_cloudcone"
                    placeholder="如 9999"
                    class="w-full px-3 py-1.5 rounded-lg bg-background border border-border font-mono text-xs focus:outline-none focus:border-primary"
                  />
                </div>
              </div>

              <div class="pt-3 border-t border-border/60">
                <button
                  type="submit"
                  :disabled="savingAff"
                  class="py-2 px-6 bg-primary text-primary-foreground font-bold rounded-lg text-xs hover:opacity-90 disabled:opacity-50 transition-all shadow-xs"
                >
                  {{ savingAff ? '保存中...' : '💾 保存所有厂商 AFF 配置' }}
                </button>
              </div>
            </form>
          </div>

          <!-- TAB 3: Crawler & Anti-Harassment Cooldown Management -->
          <div v-else-if="tab === 'crawler'" class="space-y-4">
            <!-- Cooldown Setting Box -->
            <div class="p-4 rounded-xl bg-secondary/30 border border-border space-y-3">
              <div class="space-y-1">
                <h4 class="font-bold text-foreground flex items-center gap-1.5">
                  <span>🛡️ 邮件防骚扰发信冷却（Anti-Flapping Cooldown）</span>
                </h4>
                <p class="text-[11px] text-muted-foreground leading-relaxed">
                  当某款机型短时间内频繁出现【有货/缺货/有货】来回跳变时，在此冷却周期内最多只向同一用户发送 1 封邮件，避免邮箱被轰炸。
                </p>
              </div>

              <div class="flex items-center gap-3 pt-1">
                <div class="flex items-center gap-1.5">
                  <input
                    type="number"
                    min="0"
                    max="1440"
                    v-model.number="cooldownMinutesInput"
                    class="w-24 px-3 py-1.5 rounded-lg bg-background border border-border font-mono text-xs focus:outline-none focus:border-primary text-center"
                  />
                  <span class="text-xs text-muted-foreground font-medium">分钟 (默认: 30 分钟)</span>
                </div>

                <button
                  type="button"
                  @click="saveCooldownSetting"
                  class="py-1.5 px-4 bg-secondary hover:bg-secondary/80 text-foreground border border-border font-semibold rounded-lg text-xs transition-colors"
                >
                  更新冷却时间
                </button>
              </div>
            </div>

            <!-- Crawler Status Box -->
            <div class="p-4 rounded-xl bg-secondary/30 border border-border space-y-3">
              <div class="flex items-center justify-between">
                <div>
                  <h4 class="font-bold text-foreground">实时库存与价格检测引擎</h4>
                  <p class="text-[11px] text-muted-foreground">当前检测周期：每 180 秒执行一次全网产品并发差分扫描</p>
                </div>
                <button
                  @click="triggerManualCheck"
                  :disabled="crawlerStatus.is_checking"
                  class="py-2 px-4 bg-primary text-primary-foreground font-bold rounded-lg hover:opacity-90 disabled:opacity-50 transition-all flex items-center gap-1.5"
                >
                  <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': crawlerStatus.is_checking }" />
                  <span>{{ crawlerStatus.is_checking ? '扫描检测中...' : '立即全量检测' }}</span>
                </button>
              </div>

              <div class="p-3 rounded-lg bg-background border border-border/70 text-xs font-mono space-y-1">
                <div><strong>引擎运行状态：</strong> {{ crawlerStatus.is_checking ? '🟢 正在并发扫描中...' : '⚪ 待机中' }}</div>
                <div><strong>上次扫描时间：</strong> {{ crawlerStatus.last_check_time || '—' }}</div>
                <div><strong>上次检测结果：</strong> {{ JSON.stringify(crawlerStatus.last_result || {}) }}</div>
              </div>
            </div>
          </div>

          <!-- TAB 4: Alert Logs -->
          <div v-else-if="tab === 'logs'" class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="font-bold text-foreground">最近发信审计记录 (前 50 条)</span>
              <button @click="loadAlertLogs" class="text-xs text-primary hover:underline">刷新日志</button>
            </div>

            <div class="max-h-64 overflow-y-auto space-y-1.5 pr-1">
              <div
                v-for="log in alertLogs"
                :key="log.id"
                class="p-2.5 rounded-lg bg-secondary/30 border border-border/50 font-mono text-[11px] space-y-1"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-1.5">
                    <span :class="log.status === 'sent' ? 'text-emerald-500 font-bold' : 'text-rose-500 font-bold'">
                      {{ log.status === 'sent' ? '✓ 发送成功' : '✗ 失败' }}
                    </span>
                    <span class="font-semibold text-foreground">{{ log.email }}</span>
                  </div>
                  <span class="text-muted-foreground text-[10px]">{{ log.created_at }}</span>
                </div>
                <div class="text-muted-foreground truncate">{{ log.subject }}</div>
                <div v-if="log.error_message" class="text-rose-500 text-[10px]">{{ log.error_message }}</div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { api } from '@/api'
import { useStockStore } from '@/stores/stock'
import { Settings, Lock, X, RefreshCw, Loader2 } from 'lucide-vue-next'

const props = defineProps({
  visible: Boolean,
})

const emit = defineEmits(['update:visible', 'success', 'error'])
const stockStore = useStockStore()

const isAuthenticated = ref(!!localStorage.getItem('vps_admin_token'))
const passwordInput = ref('')
const authChecking = ref(false)

const tab = ref('smtp')
const saving = ref(false)
const savingAff = ref(false)
const testingEmail = ref(false)
const testEmailInput = ref('')
const cooldownMinutesInput = ref(30)

const smtpForm = ref({
  smtp_host: '',
  smtp_port: 465,
  smtp_user: '',
  smtp_pass: '',
  smtp_pass_configured: false,
  smtp_from_name: 'VPS 实时库存与降价监控',
  smtp_from_email: '',
  smtp_ssl: true,
  smtp_tls: false,
  site_url: 'http://localhost:5173',
})

const affForm = ref({
  aff_bwh: '',
  aff_racknerd: '',
  aff_dmit: '',
  aff_clawcloud: '',
  aff_vps: '',
  aff_spartan: '',
  aff_netcup: '',
  aff_hetzner: '',
  aff_buyvm: '',
  aff_akile: '',
  aff_wikihost: '',
  aff_kurun: '',
  aff_cloudcone: '',
})

const crawlerStatus = ref({})
const alertLogs = ref([])
let crawlerPollTimer = null

watch(() => props.visible, async (newVal) => {
  if (newVal) {
    if (isAuthenticated.value) {
      await loadSettings()
      await loadCrawlerStatus()
    }
  } else {
    stopPolling()
  }
})

function close() {
  stopPolling()
  emit('update:visible', false)
}

function handleKeydown(e) {
  if (props.visible && e.key === 'Escape') {
    close()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  stopPolling()
})

function logout() {
  localStorage.removeItem('vps_admin_token')
  isAuthenticated.value = false
  passwordInput.value = ''
}

async function verifyPassword() {
  authChecking.value = true
  try {
    const res = await api.verifyAdmin(passwordInput.value)
    if (res.valid && res.token) {
      localStorage.setItem('vps_admin_token', res.token)
      isAuthenticated.value = true
      await loadSettings()
      await loadCrawlerStatus()
    }
  } catch (err) {
    emit('error', '密码错误，请重试')
  } finally {
    authChecking.value = false
  }
}

async function loadSettings() {
  try {
    let resolvedSiteUrl = cfg.site_url || ''
    if (!resolvedSiteUrl || resolvedSiteUrl.includes('localhost')) {
      if (typeof window !== 'undefined' && window.location.origin && !window.location.origin.includes('localhost')) {
        resolvedSiteUrl = window.location.origin
      } else {
        resolvedSiteUrl = 'https://vps.220360.xyz'
      }
    }

    smtpForm.value = {
      smtp_host: cfg.smtp_host || '',
      smtp_port: cfg.smtp_port || 465,
      smtp_user: cfg.smtp_user || '',
      smtp_pass: '',
      smtp_pass_configured: cfg.smtp_pass_configured,
      smtp_from_name: cfg.smtp_from_name || 'VPS 实时库存与降价监控',
      smtp_from_email: cfg.smtp_from_email || '',
      smtp_ssl: cfg.smtp_ssl !== false,
      smtp_tls: cfg.smtp_tls === true,
      site_url: resolvedSiteUrl,
    }
    testEmailInput.value = cfg.smtp_user || ''
    cooldownMinutesInput.value = cfg.notification_cooldown_minutes || 30

    // Load AFF values
    affForm.value = {
      aff_bwh: cfg.aff_bwh || '',
      aff_racknerd: cfg.aff_racknerd || '',
      aff_dmit: cfg.aff_dmit || '',
      aff_clawcloud: cfg.aff_clawcloud || '',
      aff_vps: cfg.aff_vps || '',
      aff_spartan: cfg.aff_spartan || '',
      aff_netcup: cfg.aff_netcup || '',
      aff_hetzner: cfg.aff_hetzner || '',
      aff_buyvm: cfg.aff_buyvm || '',
      aff_akile: cfg.aff_akile || '',
      aff_wikihost: cfg.aff_wikihost || '',
      aff_kurun: cfg.aff_kurun || '',
      aff_cloudcone: cfg.aff_cloudcone || '',
    }
  } catch (err) {
    console.warn('Failed to load settings:', err)
  }
}

function applyPreset(type) {
  if (type === 'qq') {
    smtpForm.value.smtp_host = 'smtp.qq.com'
    smtpForm.value.smtp_port = 465
    smtpForm.value.smtp_ssl = true
    smtpForm.value.smtp_tls = false
  } else if (type === '163') {
    smtpForm.value.smtp_host = 'smtp.163.com'
    smtpForm.value.smtp_port = 465
    smtpForm.value.smtp_ssl = true
    smtpForm.value.smtp_tls = false
  } else if (type === 'gmail') {
    smtpForm.value.smtp_host = 'smtp.gmail.com'
    smtpForm.value.smtp_port = 587
    smtpForm.value.smtp_ssl = false
    smtpForm.value.smtp_tls = true
  } else if (type === 'aliyun') {
    smtpForm.value.smtp_host = 'smtp.qiye.aliyun.com'
    smtpForm.value.smtp_port = 465
    smtpForm.value.smtp_ssl = true
    smtpForm.value.smtp_tls = false
  }
}

async function saveSmtpSettings() {
  saving.value = true
  try {
    await api.updateSettings(smtpForm.value)
    emit('success', 'SMTP 设置保存成功！')
    await loadSettings()
  } catch (err) {
    if (err.message.includes('401') || err.message.includes('凭证')) {
      logout()
      emit('error', '登录凭证已过期，请重新输入密码')
    } else {
      emit('error', err.message || '保存失败')
    }
  } finally {
    saving.value = false
  }
}

async function saveAffSettings() {
  savingAff.value = true
  try {
    await api.updateSettings(affForm.value)
    emit('success', '所有厂商 AFF 推广返利配置已保存并生效！')
    await stockStore.fetchProducts()
  } catch (err) {
    emit('error', err.message || '保存失败')
  } finally {
    savingAff.value = false
  }
}

async function saveCooldownSetting() {
  try {
    await api.updateSettings({ notification_cooldown_minutes: cooldownMinutesInput.value })
    emit('success', `防骚扰冷却时间已更新为 ${cooldownMinutesInput.value} 分钟！`)
  } catch (err) {
    emit('error', err.message || '保存失败')
  }
}

const testResult = ref(null)

async function sendTestEmail() {
  if (!testEmailInput.value) {
    testResult.value = { success: false, message: '请在输入框填写测试收件邮箱地址' }
    return
  }
  testingEmail.value = true
  testResult.value = null
  try {
    // Auto-save current form settings to database first so SMTP credentials are up to date!
    await api.updateSettings(smtpForm.value)

    const res = await api.testSmtp(testEmailInput.value)
    const successMsg = res.message || `测试邮件已成功发送至 ${testEmailInput.value}，请前往查收！`
    testResult.value = {
      success: true,
      message: successMsg,
    }
    emit('success', successMsg)
  } catch (err) {
    const errorMsg = err.message || '发信失败，请核对 SMTP 账号、端口与授权码'
    testResult.value = {
      success: false,
      message: errorMsg,
    }
    emit('error', errorMsg)
  } finally {
    testingEmail.value = false
  }
}

async function loadCrawlerStatus() {
  try {
    const status = await api.getCrawlerStatus()
    crawlerStatus.value = status
  } catch (err) {
    console.warn(err)
  }
}

function startPolling() {
  stopPolling()
  crawlerPollTimer = setInterval(async () => {
    await loadCrawlerStatus()
    if (!crawlerStatus.value.is_checking) {
      stopPolling()
    }
  }, 2000)
}

function stopPolling() {
  if (crawlerPollTimer) {
    clearInterval(crawlerPollTimer)
    crawlerPollTimer = null
  }
}

async function triggerManualCheck() {
  try {
    await api.triggerCrawler()
    emit('success', '已成功触发后台全网并发检测任务！')
    await loadCrawlerStatus()
    startPolling()
  } catch (err) {
    emit('error', err.message || '触发失败')
  }
}

async function loadAlertLogs() {
  try {
    const logs = await api.getAlertLogs(50)
    alertLogs.value = logs
  } catch (err) {
    if (err.message.includes('401')) {
      logout()
      emit('error', '请重新验证密码')
    }
  }
}
</script>

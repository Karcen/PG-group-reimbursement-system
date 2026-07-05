<template>
  <div class="login-page">
    <!-- 背景装饰 -->
    <div class="bg-gradient" />

    <!-- 登录卡片 -->
    <el-card class="login-card" shadow="always">
      <!-- 标题 -->
      <div class="login-header">
        <el-icon class="header-icon" size="40"><Money /></el-icon>
        <h1 class="login-title">实验室报销管理系统</h1>
        <p class="login-subtitle">高校科研经费报销一站式平台</p>
      </div>

      <!-- 登录表单 -->
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名或邮箱"
            size="large"
            prefix-icon="User"
            autocomplete="username"
            clearable
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            prefix-icon="Lock"
            autocomplete="current-password"
            show-password
          />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          :loading="loading"
          class="login-btn"
          @click="handleLogin"
        >
          {{ loading ? '登录中...' : '登录系统' }}
        </el-button>
      </el-form>

      <!-- 底部说明 -->
      <div class="login-footer">
        <p>首次使用请联系管理员获取账号</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    ElMessage.success(`欢迎回来，${authStore.user?.full_name || authStore.user?.username}！`)
    const redirect = route.query.redirect as string
    await router.push(redirect || '/dashboard')
  } catch {
    // 错误已由 axios 拦截器统一处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.bg-gradient {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 20% 50%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
              radial-gradient(ellipse at 80% 20%, rgba(255, 200, 100, 0.2) 0%, transparent 50%);
}

.login-card {
  width: 420px;
  padding: 12px;
  border-radius: 16px;
  position: relative;
  z-index: 1;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}
.header-icon { color: var(--el-color-primary); margin-bottom: 12px; }
.login-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 8px 0 4px;
}
.login-subtitle {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin: 0;
}

.login-form { margin-top: 16px; }

.login-btn {
  width: 100%;
  margin-top: 8px;
  letter-spacing: 1px;
  font-size: 15px;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>

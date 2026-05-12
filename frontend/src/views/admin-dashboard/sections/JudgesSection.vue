<script setup lang="ts">
// @ts-nocheck
const props = defineProps<{ ctx: any }>();
const {
  confirmClearJudges,
  confirmDeleteJudge,
  copyLink,
  exportAllJudgeQrcodes,
  getJudgeAllowedCategoryText,
  getJudgeDisplayName,
  handleCreateJudges,
  judgeQrFilenamePattern,
  judges,
  loadingJudges,
  newJudgeCount,
  openEditJudgeModal,
  showJudgeQr,
  // 编辑评委弹窗
  editJudgeModalVisible,
  closeEditJudgeModal,
  editTargetJudge,
  editJudgeForm,
  editJudgeLoading,
  handleEditJudge,
  // 二维码弹窗
  qrModalVisible,
  closeQrModal,
  qrTitle,
  qrImageUrl,
  qrTargetUrl,
  qrCurrentJudge,
  downloadCurrentQRCode,
  // 删除评委弹窗
  deleteJudgeModalVisible,
  closeDeleteJudgeModal,
  deleteTargetJudge,
  deleteJudgeConfirmPassword,
  deleteJudgeLoading,
  handleDeleteJudge,
  DELETE_CONFIRM_PASSWORD,
  // 清空评委弹窗
  clearJudgesModalVisible,
  closeClearJudgesModal,
  clearJudgesConfirmPassword,
  clearJudgesLoading,
  handleClearJudges,
  store,
} = props.ctx;
</script>

<template>
  <div class="tab-content">
    <div class="section">
      <h3>
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="8.5" cy="7" r="4" />
          <line x1="20" y1="8" x2="20" y2="14" />
          <line x1="23" y1="11" x2="17" y2="11" />
        </svg>
        创建评委
      </h3>
      <div class="create-form">
        <label class="form-field">
          <span>创建数量</span>
          <input
            v-model.number="newJudgeCount"
            type="number"
            min="1"
            class="input small-input"
          />
        </label>
        <button class="btn btn-primary" @click="handleCreateJudges">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="8.5" cy="7" r="4" />
            <line x1="20" y1="8" x2="20" y2="14" />
            <line x1="23" y1="11" x2="17" y2="11" />
          </svg>
          创建评委
        </button>
      </div>
    </div>

    <div class="section">
      <h3>
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
        评委列表
      </h3>
      <div class="qr-export-panel">
        <label class="form-field qr-pattern-field">
          <span>二维码命名规则</span>
          <input
            v-model="judgeQrFilenamePattern"
            class="input"
            placeholder="{index}_{judge_display_name}"
          />
          <small class="form-tip"
            >支持
            {index}、{judge_name}、{judge_display_name}、{site_name}</small
          >
        </label>
        <div class="button-row compact">
          <button class="btn btn-primary" @click="exportAllJudgeQrcodes">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            一键导出全部二维码
          </button>
          <button class="btn btn-danger" @click="confirmClearJudges">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polyline points="3 6 5 6 21 6" />
              <path
                d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
              />
            </svg>
            一键清空评委
          </button>
        </div>
      </div>
      <div v-if="loadingJudges" class="loading-state">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>
      <div v-else-if="!judges.length" class="empty-state">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
        <p>暂无评委</p>
      </div>
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>序号</th>
              <th>名称</th>
              <th>状态</th>
              <th>授权项目</th>
              <th>评分链接</th>
              <th>ID</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="judge in judges" :key="judge.id">
              <td>{{ judge.order }}</td>
              <td>
                <strong>{{ getJudgeDisplayName(judge) }}</strong>
              </td>
              <td>
                <span class="status-badge" :class="{ active: judge.is_active }">
                  {{ judge.is_active ? "启用" : "禁用" }}
                </span>
              </td>
              <td>{{ getJudgeAllowedCategoryText(judge) }}</td>
              <td class="ellipsis-cell">{{ judge.scoring_url }}</td>
              <td>
                <span class="id-badge">{{ judge.id }}</span>
              </td>
              <td>
                <div class="button-row compact">
                  <button
                    class="btn btn-outline mini-btn"
                    @click="openEditJudgeModal(judge)"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <path
                        d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
                      />
                      <path
                        d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"
                      />
                    </svg>
                    编辑
                  </button>
                  <button
                    class="btn btn-outline mini-btn"
                    @click="showJudgeQr(judge)"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <rect x="3" y="3" width="7" height="7" />
                      <rect x="14" y="3" width="7" height="7" />
                      <rect x="14" y="14" width="7" height="7" />
                      <rect x="3" y="14" width="7" height="7" />
                    </svg>
                    二维码
                  </button>
                  <button
                    class="btn btn-outline mini-btn"
                    @click="copyLink(judge.scoring_url)"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                      <path
                        d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
                      />
                    </svg>
                    复制链接
                  </button>
                  <button
                    class="btn btn-danger mini-btn"
                    @click="confirmDeleteJudge(judge)"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <polyline points="3 6 5 6 21 6" />
                      <path
                        d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
                      />
                      <line x1="10" y1="11" x2="10" y2="17" />
                      <line x1="14" y1="11" x2="14" y2="17" />
                    </svg>
                    删除
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- 编辑评委弹窗 -->
  <div
    v-if="editJudgeModalVisible"
    class="modal-overlay"
    @click.self="closeEditJudgeModal"
  >
    <div class="modal-card">
      <button class="modal-close" @click="closeEditJudgeModal">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
      <h3 class="modal-title">
        编辑评委 -
        {{ editTargetJudge ? getJudgeDisplayName(editTargetJudge) : "" }}
      </h3>
      <div class="modal-form">
        <label class="form-field">
          <span>评委序号</span>
          <input
            v-model.number="editJudgeForm.order"
            type="number"
            min="1"
            class="input"
            placeholder="请输入评委序号"
          />
        </label>
        <label class="form-field">
          <span>评委名称</span>
          <input
            v-model="editJudgeForm.name"
            type="text"
            class="input"
            placeholder="请输入评委名称"
            @keyup.enter="handleEditJudge"
          />
        </label>
        <div class="form-field">
          <span>可参与项目</span>
          <label class="checkbox-label">
            <input
              v-model="editJudgeForm.all_categories_allowed"
              type="checkbox"
            />
            <span class="checkbox-text">全部项目均可评分/投票</span>
          </label>
          <div
            class="category-checkbox-list"
            :class="{ disabled: editJudgeForm.all_categories_allowed }"
          >
            <label
              v-for="category in store.categories"
              :key="category.id"
              class="checkbox-label category-checkbox"
            >
              <input
                v-model="editJudgeForm.allowed_category_ids"
                type="checkbox"
                :value="category.id"
                :disabled="editJudgeForm.all_categories_allowed"
              />
              <span class="checkbox-text">{{ category.name }}</span>
            </label>
          </div>
          <small class="form-tip">
            不勾选“全部项目”时，只能访问并提交已选项目。
          </small>
        </div>
      </div>
      <div class="button-row compact">
        <button class="btn btn-outline" @click="closeEditJudgeModal">
          取消
        </button>
        <button
          class="btn btn-primary"
          :disabled="
            editJudgeLoading ||
            !editJudgeForm.name.trim() ||
            editJudgeForm.order <= 0
          "
          @click="handleEditJudge"
        >
          <span v-if="editJudgeLoading" class="spinner"></span>
          <svg
            v-else
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
            />
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
          </svg>
          {{ editJudgeLoading ? "保存中..." : "保存" }}
        </button>
      </div>
    </div>
  </div>

  <!-- 二维码弹窗 -->
  <div v-if="qrModalVisible" class="modal-overlay" @click.self="closeQrModal">
    <div class="modal-card qr-modal">
      <button class="modal-close" @click="closeQrModal">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
      <h3 class="modal-title">{{ qrTitle }}</h3>
      <div class="qr-content">
        <img :src="qrImageUrl" alt="二维码" class="qr-image" />
        <p class="qr-url">{{ qrTargetUrl }}</p>
      </div>
      <div class="button-row compact center">
        <button class="btn btn-outline" @click="closeQrModal">关闭</button>
        <button class="btn btn-primary" @click="downloadCurrentQRCode">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          下载二维码
        </button>
      </div>
    </div>
  </div>

  <!-- 删除评委确认弹窗 -->
  <div
    v-if="deleteJudgeModalVisible"
    class="modal-overlay"
    @click.self="closeDeleteJudgeModal"
  >
    <div class="modal-card delete-modal">
      <button class="modal-close" @click="closeDeleteJudgeModal">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
      <div class="delete-modal-header">
        <div class="delete-warning-icon">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
            />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </div>
        <h3>确认删除评委</h3>
      </div>
      <div class="delete-modal-content">
        <p class="delete-warning-text">
          您即将删除评委
          <strong>{{
            deleteTargetJudge ? getJudgeDisplayName(deleteTargetJudge) : ""
          }}</strong
          >，此操作不可恢复。
        </p>
        <p class="delete-hint-text">
          该评委的评分数据将被永久删除，请谨慎操作。
        </p>
        <div class="delete-password-section">
          <label class="form-field">
            <span>请输入确认密码 <code>jndx</code> 以继续</span>
            <input
              v-model="deleteJudgeConfirmPassword"
              type="password"
              class="input"
              placeholder="请输入密码"
              @keyup.enter="handleDeleteJudge"
            />
          </label>
        </div>
      </div>
      <div class="button-row compact center delete-actions">
        <button class="btn btn-outline" @click="closeDeleteJudgeModal">
          取消
        </button>
        <button
          class="btn btn-danger"
          :disabled="
            deleteJudgeLoading ||
            deleteJudgeConfirmPassword !== DELETE_CONFIRM_PASSWORD
          "
          @click="handleDeleteJudge"
        >
          <span v-if="deleteJudgeLoading" class="spinner"></span>
          <svg
            v-else
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <polyline points="3 6 5 6 21 6" />
            <path
              d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
            />
          </svg>
          {{ deleteJudgeLoading ? "删除中..." : "确认删除" }}
        </button>
      </div>
    </div>
  </div>

  <!-- 清空评委确认弹窗 -->
  <div
    v-if="clearJudgesModalVisible"
    class="modal-overlay"
    @click.self="closeClearJudgesModal"
  >
    <div class="modal-card delete-modal">
      <button class="modal-close" @click="closeClearJudgesModal">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
      <div class="delete-modal-header">
        <div class="delete-warning-icon">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
            />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </div>
        <h3>确认清空所有评委</h3>
      </div>
      <div class="delete-modal-content">
        <p class="delete-warning-text">您即将清空所有评委，此操作不可恢复。</p>
        <p class="delete-hint-text">
          所有评委及其评分数据将被永久删除，请谨慎操作。
        </p>
        <div class="delete-password-section">
          <label class="form-field">
            <span>请输入确认密码 <code>jndx</code> 以继续</span>
            <input
              v-model="clearJudgesConfirmPassword"
              type="password"
              class="input"
              placeholder="请输入密码"
              @keyup.enter="handleClearJudges"
            />
          </label>
        </div>
      </div>
      <div class="button-row compact center delete-actions">
        <button class="btn btn-outline" @click="closeClearJudgesModal">
          取消
        </button>
        <button
          class="btn btn-danger"
          :disabled="
            clearJudgesLoading ||
            clearJudgesConfirmPassword !== DELETE_CONFIRM_PASSWORD
          "
          @click="handleClearJudges"
        >
          <span v-if="clearJudgesLoading" class="spinner"></span>
          <svg
            v-else
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <polyline points="3 6 5 6 21 6" />
            <path
              d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
            />
          </svg>
          {{ clearJudgesLoading ? "清空中..." : "确认清空" }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
const props = defineProps<{ ctx: any }>();
const {
  DELETE_CONFIRM_PASSWORD,
  active,
  activeTab,
  cat,
  clearCategoriesConfirmPassword,
  clearCategoriesLoading,
  clearCategoriesModalVisible,
  clearJudgesConfirmPassword,
  clearJudgesLoading,
  clearJudgesModalVisible,
  clearParticipantsConfirmPassword,
  clearParticipantsLoading,
  clearParticipantsModalVisible,
  closeClearCategoriesModal,
  closeClearJudgesModal,
  closeClearParticipantsModal,
  closeCreateCategoryModal,
  closeCreateParticipantModal,
  closeDeleteCategoryModal,
  closeDeleteJudgeModal,
  closeDeleteParticipantModal,
  closeEditCategoryModal,
  closeEditJudgeModal,
  closeEditParticipantModal,
  closeQrModal,
  configForm,
  confirmClearParticipants,
  confirmDeleteParticipant,
  copyLink,
  createCategoryForm,
  createCategoryLoading,
  createCategoryModalVisible,
  createParticipantForm,
  createParticipantLoading,
  createParticipantModalVisible,
  deleteCategoryConfirmPassword,
  deleteCategoryLoading,
  deleteCategoryModalVisible,
  deleteJudgeConfirmPassword,
  deleteJudgeLoading,
  deleteJudgeModalVisible,
  deleteParticipantConfirmPassword,
  deleteParticipantLoading,
  deleteParticipantModalVisible,
  deleteTargetCategory,
  deleteTargetJudge,
  deleteTargetParticipant,
  downloadCurrentQRCode,
  downloadTemplate,
  editCategoryForm,
  editCategoryLoading,
  editCategoryModalVisible,
  editJudgeForm,
  editJudgeLoading,
  editJudgeModalVisible,
  editParticipantForm,
  editParticipantLoading,
  editParticipantModalVisible,
  error,
  filteredParticipants,
  handleClearCategories,
  handleClearJudges,
  handleClearParticipants,
  handleCreateCategory,
  handleCreateParticipant,
  handleDeleteCategory,
  handleDeleteJudge,
  handleDeleteParticipant,
  handleEditCategory,
  handleEditJudge,
  handleEditParticipant,
  handleExportParticipants,
  handleImport,
  handleManualImport,
  importFile,
  importResult,
  importing,
  loadingParticipants,
  manualImportData,
  manualImportResult,
  manualImporting,
  onImportFileChange,
  openCreateParticipantModal,
  openEditParticipantModal,
  participant,
  participantCategoryFilter,
  participantSortKey,
  participantSortOrder,
  qrImageUrl,
  qrModalVisible,
  qrTargetUrl,
  qrTitle,
  saveConfig,
  savingConfig,
  store,
  success,
  toggleParticipantSort,
  useNewCategory,
} = props.ctx;
</script>

<template>
  <div class="tab-content">
    <!-- 选手列表 -->
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
        选手列表
      </h3>
      <div class="qr-export-panel">
        <div class="participant-stats">
          <span class="stat-item"
            >共 {{ filteredParticipants.length }} 名选手</span
          >
          <span
            v-if="participantCategoryFilter !== ''"
            class="stat-item filter-active"
            >(已筛选)</span
          >
        </div>
        <div class="button-row">
          <button class="btn btn-primary" @click="openCreateParticipantModal">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M12 4v16m8-8H4" />
            </svg>
            添加选手
          </button>
          <button class="btn btn-outline" @click="handleExportParticipants">
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
            导出选手
          </button>
          <button class="btn btn-danger" @click="confirmClearParticipants">
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
            一键清空选手
          </button>
        </div>
      </div>
      <!-- 类别筛选 -->
      <div class="filter-panel">
        <label class="form-field">
          <span>类别筛选</span>
          <select v-model="participantCategoryFilter" class="input">
            <option value="">全部类别</option>
            <option
              v-for="cat in store.categories"
              :key="cat.id"
              :value="cat.id"
            >
              {{ cat.name }}
            </option>
          </select>
        </label>
      </div>
      <div v-if="loadingParticipants" class="loading-state">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>
      <div v-else-if="!filteredParticipants.length" class="empty-state">
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
        <p>暂无选手</p>
      </div>
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th
                class="sortable"
                :class="{ active: participantSortKey === 'order' }"
                @click="toggleParticipantSort"
              >
                序号
                <span class="sort-indicator">
                  {{
                    participantSortKey === "order"
                      ? participantSortOrder === "asc"
                        ? "↑"
                        : "↓"
                      : ""
                  }}
                </span>
              </th>
              <th>ID</th>
              <th>姓名</th>
              <th>学院</th>
              <th>类别</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="participant in filteredParticipants"
              :key="participant.id"
            >
              <td>{{ participant.order }}</td>
              <td>
                <span class="id-badge">{{ participant.id }}</span>
              </td>
              <td>
                <strong>{{ participant.name }}</strong>
              </td>
              <td>{{ participant.college || "-" }}</td>
              <td>{{ participant.category_name }}</td>
              <td>
                <div class="button-row compact">
                  <button
                    class="btn btn-outline mini-btn"
                    @click="openEditParticipantModal(participant)"
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
                    class="btn btn-danger mini-btn"
                    @click="confirmDeleteParticipant(participant)"
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

    <div class="section">
      <h3>
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
          />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
          <polyline points="10 9 9 9 8 9" />
        </svg>
        Excel 导入
      </h3>

      <div class="field-settings-panel">
        <div class="field-settings-header">
          <div>
            <h4>字段名手动设置</h4>
          </div>
          <button
            class="btn btn-outline"
            :disabled="savingConfig"
            @click="saveConfig"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"
              />
              <polyline points="17 21 17 13 7 13 7 21" />
              <polyline points="7 3 7 8 15 8" />
            </svg>
            {{ savingConfig ? "保存中..." : "保存字段设置" }}
          </button>
        </div>
        <div class="form-grid">
          <label class="form-field">
            <span>选手 Sheet 名称</span>
            <input
              v-model="configForm.participant_sheet_name"
              class="input"
              placeholder="选手数据"
            />
          </label>
          <label class="form-field">
            <span>类别字段名</span>
            <input
              v-model="configForm.category_field_name"
              class="input"
              placeholder="类别"
            />
          </label>
          <label class="form-field">
            <span>选手字段名</span>
            <input
              v-model="configForm.participant_field_name"
              class="input"
              placeholder="选手"
            />
          </label>
          <label class="form-field">
            <span>序号字段名</span>
            <input
              v-model="configForm.order_field_name"
              class="input"
              placeholder="序号"
            />
          </label>
          <label class="form-field">
            <span>学院字段名</span>
            <input
              v-model="configForm.college_field_name"
              class="input"
              placeholder="学院"
            />
          </label>
        </div>
      </div>

      <div class="import-actions">
        <button class="btn btn-outline" @click="downloadTemplate">
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
          下载 Excel 模板
        </button>
        <label class="file-input-wrapper btn btn-outline">
          <input
            type="file"
            class="file-input"
            accept=".xlsx,.xlsm,.xltx,.xltm"
            @change="onImportFileChange"
          />
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          {{ importFile ? importFile.name : "选择 Excel 文件" }}
        </label>
      </div>

      <div
        v-if="importResult"
        class="message-box"
        :class="{
          success: importResult.includes('成功'),
          error: importResult.includes('失败') || importResult.includes('错误'),
        }"
      >
        <svg
          v-if="importResult.includes('成功')"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <polyline points="20 6 9 17 4 12" />
        </svg>
        <svg
          v-else
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        {{ importResult }}
      </div>

      <div class="button-row">
        <button
          class="btn btn-primary"
          :disabled="importing || !importFile"
          @click="handleImport"
        >
          <span v-if="importing" class="spinner"></span>
          <svg
            v-else
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
            />
            <polyline points="14 2 14 8 20 8" />
            <line x1="12" y1="18" x2="12" y2="12" />
            <line x1="9" y1="15" x2="15" y2="15" />
          </svg>
          {{ importing ? "导入中..." : "开始导入 Excel" }}
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
          <path
            d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
          />
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
        </svg>
        手动录入
      </h3>
      <p class="section-desc">
        直接输入选手数据，每行一个，格式：类别,选手姓名,序号,学院
      </p>

      <div class="manual-import-form">
        <label class="form-field">
          <span>选手数据（每行一个）</span>
          <textarea
            v-model="manualImportData"
            class="textarea manual-input"
            rows="10"
            placeholder="歌唱组,张三,1,音乐学院&#10;歌唱组,李四,2,音乐学院&#10;舞蹈组,王五,1,舞蹈学院&#10;舞蹈组,赵六,2,舞蹈学院"
          />
        </label>
        <div class="form-tip">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
          支持格式： 类别,选手姓名,序号,学院。序号用于控制同一类别内的展示顺序。
        </div>
      </div>

      <div
        v-if="manualImportResult"
        class="message-box"
        :class="{
          success: manualImportResult.includes('成功'),
          error:
            manualImportResult.includes('失败') ||
            manualImportResult.includes('错误'),
        }"
      >
        <svg
          v-if="manualImportResult.includes('成功')"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <polyline points="20 6 9 17 4 12" />
        </svg>
        <svg
          v-else
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        {{ manualImportResult }}
      </div>

      <div class="button-row">
        <button
          class="btn btn-primary"
          :disabled="manualImporting || !manualImportData.trim()"
          @click="handleManualImport"
        >
          <span v-if="manualImporting" class="spinner"></span>
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
          {{ manualImporting ? "导入中..." : "开始手动导入" }}
        </button>
      </div>
    </div>
  </div>

  <div v-if="qrModalVisible" class="modal-overlay" @click.self="closeQrModal">
    <div class="modal-card">
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
      <h3>{{ qrTitle }}</h3>
      <div class="qr-wrapper">
        <img :src="qrImageUrl" alt="二维码" class="qr-image" />
      </div>
      <p class="qr-url">{{ qrTargetUrl }}</p>
      <div class="button-row compact center">
        <button class="btn btn-primary" @click="copyLink(qrTargetUrl)">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
          </svg>
          复制链接
        </button>
        <button class="btn btn-outline" @click="downloadCurrentQRCode">
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
      <h3>编辑评委</h3>
      <div class="form-grid">
        <label class="form-field">
          <span>序号</span>
          <input
            v-model.number="editJudgeForm.order"
            class="input"
            type="number"
            min="1"
            placeholder="请输入评委序号"
          />
        </label>
        <label class="form-field">
          <span>姓名</span>
          <input
            v-model="editJudgeForm.name"
            class="input"
            placeholder="请输入评委姓名"
          />
        </label>
      </div>
      <div class="button-row compact center" style="margin-top: 24px">
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
            deleteTargetJudge?.name || `评委${deleteTargetJudge?.id}`
          }}</strong
          >，此操作不可恢复。
        </p>
        <p class="delete-hint-text">
          该评委的所有评分数据将被永久删除，请谨慎操作。
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

  <!-- 删除选手确认弹窗 -->
  <div
    v-if="deleteParticipantModalVisible"
    class="modal-overlay"
    @click.self="closeDeleteParticipantModal"
  >
    <div class="modal-card delete-modal">
      <button class="modal-close" @click="closeDeleteParticipantModal">
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
        <h3>确认删除选手</h3>
      </div>
      <div class="delete-modal-content">
        <p class="delete-warning-text">
          您即将删除选手
          <strong>{{ deleteTargetParticipant?.name }}</strong
          >，此操作不可恢复。
        </p>
        <p class="delete-hint-text">
          该选手的所有评分数据将被永久删除，请谨慎操作。
        </p>
        <div class="delete-password-section">
          <label class="form-field">
            <span>请输入确认密码 <code>jndx</code> 以继续</span>
            <input
              v-model="deleteParticipantConfirmPassword"
              type="password"
              class="input"
              placeholder="请输入密码"
              @keyup.enter="handleDeleteParticipant"
            />
          </label>
        </div>
      </div>
      <div class="button-row compact center delete-actions">
        <button class="btn btn-outline" @click="closeDeleteParticipantModal">
          取消
        </button>
        <button
          class="btn btn-danger"
          :disabled="
            deleteParticipantLoading ||
            deleteParticipantConfirmPassword !== DELETE_CONFIRM_PASSWORD
          "
          @click="handleDeleteParticipant"
        >
          <span v-if="deleteParticipantLoading" class="spinner"></span>
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
          {{ deleteParticipantLoading ? "删除中..." : "确认删除" }}
        </button>
      </div>
    </div>
  </div>

  <!-- 清空选手确认弹窗 -->
  <div
    v-if="clearParticipantsModalVisible"
    class="modal-overlay"
    @click.self="closeClearParticipantsModal"
  >
    <div class="modal-card delete-modal">
      <button class="modal-close" @click="closeClearParticipantsModal">
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
        <h3>确认清空所有选手</h3>
      </div>
      <div class="delete-modal-content">
        <p class="delete-warning-text">
          您即将<strong>清空所有选手</strong>，此操作不可恢复。
        </p>
        <p class="delete-hint-text">
          所有选手及其评分数据将被永久删除，请谨慎操作。
        </p>
        <div class="delete-password-section">
          <label class="form-field">
            <span>请输入确认密码 <code>jndx</code> 以继续</span>
            <input
              v-model="clearParticipantsConfirmPassword"
              type="password"
              class="input"
              placeholder="请输入密码"
              @keyup.enter="handleClearParticipants"
            />
          </label>
        </div>
      </div>
      <div class="button-row compact center delete-actions">
        <button class="btn btn-outline" @click="closeClearParticipantsModal">
          取消
        </button>
        <button
          class="btn btn-danger"
          :disabled="
            clearParticipantsLoading ||
            clearParticipantsConfirmPassword !== DELETE_CONFIRM_PASSWORD
          "
          @click="handleClearParticipants"
        >
          <span v-if="clearParticipantsLoading" class="spinner"></span>
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
          {{ clearParticipantsLoading ? "清空中..." : "确认清空" }}
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
        <p class="delete-warning-text">
          您即将<strong>清空所有评委</strong>，此操作不可恢复。
        </p>
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
              d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 0 0 1 2 2v2"
            />
          </svg>
          {{ clearJudgesLoading ? "清空中..." : "确认清空" }}
        </button>
      </div>
    </div>
  </div>

  <!-- 清空类别确认弹窗 -->
  <div
    v-if="clearCategoriesModalVisible"
    class="modal-overlay"
    @click.self="closeClearCategoriesModal"
  >
    <div class="modal-card delete-modal">
      <button class="modal-close" @click="closeClearCategoriesModal">
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
        <h3>确认清空所有类别</h3>
      </div>
      <div class="delete-modal-content">
        <p class="delete-warning-text">
          您即将<strong>清空所有类别</strong>，此操作不可恢复。
        </p>
        <p class="delete-hint-text">
          所有类别及其关联的选手、评分数据将被永久删除，请谨慎操作。
        </p>
        <div class="delete-password-section">
          <label class="form-field">
            <span>请输入确认密码 <code>jndx</code> 以继续</span>
            <input
              v-model="clearCategoriesConfirmPassword"
              type="password"
              class="input"
              placeholder="请输入密码"
              @keyup.enter="handleClearCategories"
            />
          </label>
        </div>
      </div>
      <div class="button-row compact center delete-actions">
        <button class="btn btn-outline" @click="closeClearCategoriesModal">
          取消
        </button>
        <button
          class="btn btn-danger"
          :disabled="
            clearCategoriesLoading ||
            clearCategoriesConfirmPassword !== DELETE_CONFIRM_PASSWORD
          "
          @click="handleClearCategories"
        >
          <span v-if="clearCategoriesLoading" class="spinner"></span>
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
          {{ clearCategoriesLoading ? "清空中..." : "确认清空" }}
        </button>
      </div>
    </div>
  </div>

  <!-- 编辑选手弹窗 -->
  <div
    v-if="editParticipantModalVisible"
    class="modal-overlay"
    @click.self="closeEditParticipantModal"
  >
    <div class="modal-card">
      <button class="modal-close" @click="closeEditParticipantModal">
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
      <h3>编辑选手</h3>
      <div class="form-grid">
        <label class="form-field">
          <span>姓名</span>
          <input
            v-model="editParticipantForm.name"
            class="input"
            placeholder="请输入选手姓名"
          />
        </label>
        <label class="form-field">
          <span>类别</span>
          <select v-model="editParticipantForm.category_id" class="input">
            <option
              v-for="cat in store.categories"
              :key="cat.id"
              :value="cat.id"
            >
              {{ cat.name }}
            </option>
          </select>
        </label>
        <label class="form-field">
          <span>序号</span>
          <input
            v-model.number="editParticipantForm.order"
            class="input"
            type="number"
            placeholder="请输入序号"
          />
        </label>
        <label class="form-field">
          <span>学院</span>
          <input
            v-model="editParticipantForm.college"
            class="input"
            placeholder="请输入学院"
          />
        </label>
      </div>
      <div class="button-row compact center" style="margin-top: 24px">
        <button class="btn btn-outline" @click="closeEditParticipantModal">
          取消
        </button>
        <button
          class="btn btn-primary"
          :disabled="editParticipantLoading || !editParticipantForm.name.trim()"
          @click="handleEditParticipant"
        >
          <span v-if="editParticipantLoading" class="spinner"></span>
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
          {{ editParticipantLoading ? "保存中..." : "保存" }}
        </button>
      </div>
    </div>
  </div>

  <!-- 创建选手弹窗 -->
  <div
    v-if="createParticipantModalVisible"
    class="modal-overlay"
    @click.self="closeCreateParticipantModal"
  >
    <div class="modal-card">
      <button class="modal-close" @click="closeCreateParticipantModal">
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
      <h3 class="modal-title">添加选手</h3>
      <div class="modal-form">
        <label class="form-field">
          <span>选手姓名</span>
          <input
            v-model="createParticipantForm.name"
            type="text"
            class="input"
            placeholder="请输入选手姓名"
            @keyup.enter="handleCreateParticipant"
          />
        </label>
        <label class="form-field">
          <span>类别选择</span>
          <div class="switch-list inline-switch-list">
            <label class="switch-item">
              <div class="switch">
                <input v-model="useNewCategory" type="checkbox" />
                <span class="slider"></span>
              </div>
              <span class="switch-label">创建新类别</span>
            </label>
          </div>
        </label>
        <label v-if="!useNewCategory" class="form-field">
          <span>选择类别</span>
          <select v-model="createParticipantForm.category_id" class="input">
            <option
              v-for="cat in store.categories"
              :key="cat.id"
              :value="cat.id"
            >
              {{ cat.name }}
            </option>
          </select>
        </label>
        <label v-if="useNewCategory" class="form-field">
          <span>新类别名称</span>
          <input
            v-model="createParticipantForm.category_name"
            type="text"
            class="input"
            placeholder="请输入新类别名称"
          />
        </label>
        <label class="form-field">
          <span>序号</span>
          <input
            v-model.number="createParticipantForm.order"
            type="number"
            class="input"
            placeholder="留空自动分配"
          />
        </label>
        <label class="form-field">
          <span>学院</span>
          <input
            v-model="createParticipantForm.college"
            type="text"
            class="input"
            placeholder="请输入学院（可选）"
          />
        </label>
      </div>
      <div class="button-row compact">
        <button class="btn btn-outline" @click="closeCreateParticipantModal">
          取消
        </button>
        <button
          class="btn btn-primary"
          :disabled="
            createParticipantLoading || !createParticipantForm.name.trim()
          "
          @click="handleCreateParticipant"
        >
          <span v-if="createParticipantLoading" class="spinner"></span>
          <svg
            v-else
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M12 4v16m8-8H4" />
          </svg>
          {{ createParticipantLoading ? "创建中..." : "创建" }}
        </button>
      </div>
    </div>
  </div>

  <!-- 创建类别弹窗 -->
  <div
    v-if="createCategoryModalVisible"
    class="modal-overlay"
    @click.self="closeCreateCategoryModal"
  >
    <div class="modal-card">
      <button class="modal-close" @click="closeCreateCategoryModal">
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
      <h3 class="modal-title">添加类别</h3>
      <div class="modal-form">
        <label class="form-field">
          <span>类别名称</span>
          <input
            v-model="createCategoryForm.name"
            type="text"
            class="input"
            placeholder="请输入类别名称"
            @keyup.enter="handleCreateCategory"
          />
        </label>
        <label class="form-field">
          <span>排序</span>
          <input
            v-model.number="createCategoryForm.order"
            type="number"
            class="input"
            placeholder="数字越小越靠前"
          />
        </label>
        <label class="form-field full-width">
          <span>打分模式</span>
          <select v-model="createCategoryForm.scoring_mode" class="input">
            <option value="default">使用全局设置</option>
            <option value="score">分数模式</option>
            <option value="vote">投票模式</option>
          </select>
        </label>
        <template
          v-if="
            createCategoryForm.scoring_mode === 'vote' ||
            (createCategoryForm.scoring_mode === 'default' &&
              configForm.scoring_mode === 'vote')
          "
        >
          <label class="form-field">
            <span>投票总数（该类别的选手人数，创建后将自动更新）</span>
            <input
              type="number"
              min="1"
              class="input"
              placeholder="将根据添加的选手自动设置"
              disabled
            />
          </label>
          <label class="form-field">
            <span>选择人数（评委要选多少人）</span>
            <input
              v-model.number="createCategoryForm.vote_select_count"
              type="number"
              min="1"
              class="input"
              placeholder="选择多少人"
            />
          </label>
        </template>
        <label class="form-field">
          <span>描述</span>
          <textarea
            v-model="createCategoryForm.description"
            class="input"
            rows="3"
            placeholder="类别描述（可选）"
          ></textarea>
        </label>
      </div>
      <div class="button-row compact">
        <button class="btn btn-outline" @click="closeCreateCategoryModal">
          取消
        </button>
        <button
          class="btn btn-primary"
          :disabled="createCategoryLoading || !createCategoryForm.name.trim()"
          @click="handleCreateCategory"
        >
          <span v-if="createCategoryLoading" class="spinner"></span>
          <svg
            v-else
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M12 4v16m8-8H4" />
          </svg>
          {{ createCategoryLoading ? "创建中..." : "创建" }}
        </button>
      </div>
    </div>
  </div>

  <!-- 编辑类别弹窗 -->
  <div
    v-if="editCategoryModalVisible"
    class="modal-overlay"
    @click.self="closeEditCategoryModal"
  >
    <div class="modal-card">
      <button class="modal-close" @click="closeEditCategoryModal">
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
      <h3 class="modal-title">编辑类别</h3>
      <div class="modal-form">
        <label class="form-field">
          <span>类别名称</span>
          <input
            v-model="editCategoryForm.name"
            type="text"
            class="input"
            placeholder="请输入类别名称"
            @keyup.enter="handleEditCategory"
          />
        </label>
        <label class="form-field">
          <span>排序</span>
          <input
            v-model.number="editCategoryForm.order"
            type="number"
            class="input"
            placeholder="数字越小越靠前"
          />
        </label>
        <label class="form-field full-width">
          <span>打分模式</span>
          <select v-model="editCategoryForm.scoring_mode" class="input">
            <option value="default">使用全局设置</option>
            <option value="score">分数模式</option>
            <option value="vote">投票模式</option>
          </select>
        </label>
        <template
          v-if="
            editCategoryForm.scoring_mode === 'vote' ||
            (editCategoryForm.scoring_mode === 'default' &&
              configForm.scoring_mode === 'vote')
          "
        >
          <label class="form-field">
            <span>投票总数（该类别的选手人数）</span>
            <input
              :value="editCategoryForm.vote_total_count"
              type="number"
              min="1"
              class="input"
              readonly
              placeholder="该类别的选手人数"
            />
          </label>
          <label class="form-field">
            <span>选择人数（评委要选多少人）</span>
            <input
              v-model.number="editCategoryForm.vote_select_count"
              type="number"
              min="1"
              class="input"
              placeholder="选择多少人"
            />
          </label>
        </template>
        <label class="form-field">
          <span>描述</span>
          <textarea
            v-model="editCategoryForm.description"
            class="input"
            rows="3"
            placeholder="类别描述（可选）"
          ></textarea>
        </label>
      </div>
      <div class="button-row compact">
        <button class="btn btn-outline" @click="closeEditCategoryModal">
          取消
        </button>
        <button
          class="btn btn-primary"
          :disabled="editCategoryLoading || !editCategoryForm.name.trim()"
          @click="handleEditCategory"
        >
          <span v-if="editCategoryLoading" class="spinner"></span>
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
          {{ editCategoryLoading ? "保存中..." : "保存" }}
        </button>
      </div>
    </div>
  </div>

  <!-- 删除类别确认弹窗 -->
  <div
    v-if="deleteCategoryModalVisible"
    class="modal-overlay"
    @click.self="closeDeleteCategoryModal"
  >
    <div class="modal-card delete-modal">
      <button class="modal-close" @click="closeDeleteCategoryModal">
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
        <h3>确认删除类别</h3>
      </div>
      <div class="delete-modal-content">
        <p class="delete-warning-text">
          您即将删除类别
          <strong>{{ deleteTargetCategory?.name }}</strong
          >，此操作不可恢复。
        </p>
        <p class="delete-hint-text">
          该类别下的所有选手及其评分数据将被永久删除，请谨慎操作。
        </p>
        <div class="delete-password-section">
          <label class="form-field">
            <span>请输入确认密码 <code>jndx</code> 以继续</span>
            <input
              v-model="deleteCategoryConfirmPassword"
              type="password"
              class="input"
              placeholder="请输入密码"
              @keyup.enter="handleDeleteCategory"
            />
          </label>
        </div>
      </div>
      <div class="button-row compact center delete-actions">
        <button class="btn btn-outline" @click="closeDeleteCategoryModal">
          取消
        </button>
        <button
          class="btn btn-danger"
          :disabled="
            deleteCategoryLoading ||
            deleteCategoryConfirmPassword !== DELETE_CONFIRM_PASSWORD
          "
          @click="handleDeleteCategory"
        >
          <span v-if="deleteCategoryLoading" class="spinner"></span>
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
          {{ deleteCategoryLoading ? "删除中..." : "确认删除" }}
        </button>
      </div>
    </div>
  </div>

  <!-- 类别管理标签页 -->
</template>

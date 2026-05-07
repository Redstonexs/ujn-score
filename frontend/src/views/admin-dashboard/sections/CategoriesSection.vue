<script setup lang="ts">
// @ts-nocheck
const props = defineProps<{ ctx: any }>();
const {
  confirmClearCategories,
  confirmDeleteCategory,
  openCreateCategoryModal,
  openEditCategoryModal,
  store,
  createCategoryModalVisible,
  closeCreateCategoryModal,
  createCategoryForm,
  createCategoryLoading,
  handleCreateCategory,
  editCategoryModalVisible,
  closeEditCategoryModal,
  editCategoryForm,
  editCategoryLoading,
  handleEditCategory,
  deleteCategoryModalVisible,
  closeDeleteCategoryModal,
  deleteTargetCategory,
  deleteCategoryConfirmPassword,
  deleteCategoryLoading,
  handleDeleteCategory,
  DELETE_CONFIRM_PASSWORD,
  clearCategoriesModalVisible,
  closeClearCategoriesModal,
  clearCategoriesConfirmPassword,
  clearCategoriesLoading,
  handleClearCategories,
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
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
        </svg>
        类别列表
      </h3>
      <div class="qr-export-panel">
        <div class="participant-stats">
          <span class="stat-item">共 {{ store.categories.length }} 个类别</span>
        </div>
        <div class="button-row">
          <button class="btn btn-primary" @click="openCreateCategoryModal">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M12 4v16m8-8H4" />
            </svg>
            添加类别
          </button>
          <button
            v-if="store.categories.length"
            class="btn btn-danger"
            @click="confirmClearCategories"
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
            清空类别
          </button>
        </div>
      </div>
      <div v-if="!store.categories.length" class="empty-state">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
        </svg>
        <p>暂无类别</p>
      </div>
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>类别名称</th>
              <th>打分模式</th>
              <th>选手数量</th>
              <th>描述</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="category in store.categories" :key="category.id">
              <td>
                <span class="id-badge">{{ category.id }}</span>
              </td>
              <td>
                <strong>{{ category.name }}</strong>
              </td>
              <td>
                <span
                  class="status-badge"
                  :class="{ active: category.scoring_mode === 'vote' }"
                >
                  {{
                    category.scoring_mode === "vote"
                      ? "投票模式"
                      : "分数模式"
                  }}
                </span>
              </td>
              <td>{{ category.participant_count }}</td>
              <td>{{ category.description || "-" }}</td>
              <td>
                <div class="button-row compact">
                  <button
                    class="btn btn-outline mini-btn"
                    @click="openEditCategoryModal(category)"
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
                    @click="confirmDeleteCategory(category)"
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

  <!-- 添加类别弹窗 -->
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
        <p class="delete-warning-text">您即将清空所有类别，此操作不可恢复。</p>
        <p class="delete-hint-text">
          所有类别及其下的选手、评分数据将被永久删除，请谨慎操作。
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
</template>

<script setup lang="ts">
// @ts-nocheck
const props = defineProps<{ ctx: any }>();
const {
  connectSSE,
  disconnectSSE,
  getJudgeCategoryCompletedCount,
  getJudgeCategoryProgressPercent,
  getJudgeScoreStatus,
  getJudgeVoteCount,
  getJudgeVoteStatus,
  isJudgeAllowedForCategory,
  getParticipantRank,
  getParticipantStat,
  getSortState,
  getSortedParticipants,
  handleExport,
  handleExportScoreDetails,
  loadScores,
  loadingScores,
  scoresData,
  sseStatus,
  toggleSort,
} = props.ctx;

function formatDroppedScores(stat: any, field: "dropped_lows" | "dropped_highs") {
  const values = stat?.[field] || [];
  return values.length ? values.join("、") : "-";
}

function getJudgeCountText(categoryId: number, stat: any) {
  if (!stat) return "-";
  const allowedJudgeCount = (scoresData.value?.judges || []).filter((judge: any) =>
    isJudgeAllowedForCategory(categoryId, judge),
  ).length;
  return `${stat.count}/${allowedJudgeCount || stat.count}`;
}
</script>

<template>
  <div class="tab-content">
    <div class="section-actions">
      <div class="sse-status-group">
        <span
          class="sse-status-badge"
          :class="{
            connected: sseStatus === 'connected',
            connecting: sseStatus === 'connecting',
            disconnected: sseStatus === 'disconnected',
          }"
        >
          <span class="sse-dot"></span>
          <span v-if="sseStatus === 'connected'">实时更新中</span>
          <span v-else-if="sseStatus === 'connecting'">连接中…</span>
          <span v-else>已断开</span>
        </span>
        <button
          v-if="sseStatus === 'disconnected'"
          class="btn btn-outline btn-sm"
          @click="connectSSE"
          title="重新连接实时更新"
        >
          重连
        </button>
      </div>
      <button class="btn btn-outline" @click="loadScores">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <polyline points="23 4 23 10 17 10" />
          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
        </svg>
        刷新
      </button>
      <button class="btn btn-outline" @click="handleExportScoreDetails">
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
        导出分数明细
      </button>
      <button class="btn btn-primary" @click="handleExport">
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
        导出排名
      </button>
    </div>

    <div class="section" v-if="loadingScores">
      <div class="loading-state">
        <div class="spinner"></div>
        <p>正在加载评分数据...</p>
      </div>
    </div>
    <template v-else-if="scoresData">
      <div class="section">
        <h3>
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
          评委完成情况
        </h3>
        <div
          v-for="category in scoresData.categories"
          :key="`progress-${category.id}`"
          class="progress-matrix-section"
        >
          <div class="progress-matrix-header">
            <div>
              <h4>{{ category.name }}</h4>
              <p v-if="category.mode === 'vote'">显示每位评委的投票完成情况</p>
              <p v-else>显示每位评委对每位选手是否已打分</p>
            </div>
          </div>
          <div class="table-wrap">
            <table class="data-table progress-matrix-table">
              <thead>
                <tr v-if="category.mode === 'vote'">
                  <th>评委</th>
                  <th>投票状态</th>
                  <th>已投人数</th>
                  <th>完成度</th>
                </tr>
                <tr v-else>
                  <th>评委</th>
                  <th
                    v-for="participant in category.participants"
                    :key="participant.id"
                  >
                    {{ participant.name }}
                  </th>
                  <th>完成度</th>
                </tr>
              </thead>
              <tbody>
                <template v-if="category.mode === 'vote'">
                  <tr
                    v-for="judge in scoresData.judges"
                    :key="`${category.id}-${judge.id}`"
                  >
                    <td>
                      <div class="judge-name-cell">{{ judge.name }}</div>
                    </td>
                    <td>
                      <span
                        class="status-badge"
                        :class="{
                          active:
                            isJudgeAllowedForCategory(category.id, judge) &&
                            getJudgeVoteStatus(category.id, judge.id),
                        }"
                      >
                        {{
                          !isJudgeAllowedForCategory(category.id, judge)
                            ? "不参与"
                            : getJudgeVoteStatus(category.id, judge.id)
                            ? "已完成"
                            : "未完成"
                        }}
                      </span>
                    </td>
                    <td>
                      {{
                        isJudgeAllowedForCategory(category.id, judge)
                          ? getJudgeVoteCount(category.id, judge.id)
                          : "-"
                      }}
                    </td>
                    <td class="progress-summary-cell">
                      <div class="progress-summary-content">
                        <span class="progress-fraction">
                          {{
                            !isJudgeAllowedForCategory(category.id, judge)
                              ? "-"
                              : getJudgeVoteStatus(category.id, judge.id)
                              ? "1/1"
                              : "0/1"
                          }}
                        </span>
                        <div class="progress-bar-wrapper">
                          <div class="progress-bar">
                            <div
                              class="progress-bar-fill"
                              :class="{
                                low: !getJudgeVoteStatus(category.id, judge.id),
                                active:
                                  isJudgeAllowedForCategory(category.id, judge) &&
                                  getJudgeVoteStatus(category.id, judge.id),
                              }"
                              :style="{
                                width:
                                  isJudgeAllowedForCategory(category.id, judge) &&
                                  getJudgeVoteStatus(category.id, judge.id)
                                    ? '100%'
                                    : '0%',
                              }"
                            ></div>
                          </div>
                          <span class="progress-text">
                            {{
                              !isJudgeAllowedForCategory(category.id, judge)
                                ? "-"
                                : getJudgeVoteStatus(category.id, judge.id)
                                ? "100%"
                                : "0%"
                            }}
                          </span>
                        </div>
                      </div>
                    </td>
                  </tr>
                </template>
                <template v-else>
                  <tr
                    v-for="judge in scoresData.judges"
                    :key="`${category.id}-${judge.id}`"
                  >
                    <td>
                      <div class="judge-name-cell">{{ judge.name }}</div>
                    </td>
                    <td
                      v-for="participant in category.participants"
                      :key="`${judge.id}-${participant.id}`"
                    >
                      <span
                        class="status-badge"
                        :class="{
                          active:
                            isJudgeAllowedForCategory(category.id, judge) &&
                            getJudgeScoreStatus(
                              category.id,
                              judge.id,
                              participant.id,
                            ),
                        }"
                      >
                        {{
                          !isJudgeAllowedForCategory(category.id, judge)
                            ? "不参与"
                            : getJudgeScoreStatus(
                                category.id,
                                judge.id,
                                participant.id,
                              )
                            ? "已打分"
                            : "未打分"
                        }}
                      </span>
                    </td>
                    <td class="progress-summary-cell">
                      <div class="progress-summary-content">
                        <span class="progress-fraction">
                          {{
                            isJudgeAllowedForCategory(category.id, judge)
                              ? `${getJudgeCategoryCompletedCount(category, judge.id)}/${category.participants.length}`
                              : "-"
                          }}
                        </span>
                        <div class="progress-bar-wrapper">
                          <div class="progress-bar">
                            <div
                              class="progress-bar-fill"
                              :class="{
                                low:
                                  getJudgeCategoryProgressPercent(
                                    category,
                                    judge.id,
                                  ) < 30,
                                partial:
                                  getJudgeCategoryProgressPercent(
                                    category,
                                    judge.id,
                                  ) >= 30 &&
                                  getJudgeCategoryProgressPercent(
                                    category,
                                    judge.id,
                                  ) < 70,
                              }"
                              :style="{
                                width:
                                  isJudgeAllowedForCategory(category.id, judge)
                                    ? getJudgeCategoryProgressPercent(
                                        category,
                                        judge.id,
                                      ) + '%'
                                    : '0%',
                              }"
                            ></div>
                          </div>
                          <span class="progress-text">
                            {{
                              isJudgeAllowedForCategory(category.id, judge)
                                ? getJudgeCategoryProgressPercent(
                                    category,
                                    judge.id,
                                  ) + "%"
                                : "-"
                            }}
                          </span>
                        </div>
                      </div>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div
        v-for="category in scoresData.categories"
        :key="category.id"
        class="section"
      >
        <h3>
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
          {{ category.name }} 排名
        </h3>
        <p class="rule-text">
          {{
            scoresData.category_rules?.[category.id] ||
            scoresData.calculation_rule
          }}
        </p>
        <div v-if="!category.participants?.length" class="empty-state">
          <p>暂无选手数据</p>
        </div>
        <div v-else class="table-wrap">
          <table class="data-table ranking-table">
            <thead>
              <tr v-if="category.mode === 'vote'">
                <th class="col-rank">排名</th>
                <th
                  class="col-order sortable"
                  :class="{
                    active: getSortState(category.id).key === 'order',
                  }"
                  @click="toggleSort(category.id, 'order')"
                >
                  选手序号
                  <span class="sort-indicator">
                    {{
                      getSortState(category.id).key === "order"
                        ? getSortState(category.id).order === "asc"
                          ? "↑"
                          : "↓"
                        : ""
                    }}
                  </span>
                </th>
                <th>选手</th>
                <th>学院</th>
                <th
                  class="col-score sortable"
                  :class="{
                    active: getSortState(category.id).key === 'score',
                  }"
                  @click="toggleSort(category.id, 'score')"
                >
                  票数
                  <span class="sort-indicator">
                    {{
                      getSortState(category.id).key === "score"
                        ? getSortState(category.id).order === "asc"
                          ? "↑"
                          : "↓"
                        : ""
                    }}
                  </span>
                </th>
                <th class="col-score">得票率</th>
              </tr>
              <tr v-else>
                <th class="col-rank">排名</th>
                <th
                  class="col-order sortable"
                  :class="{
                    active: getSortState(category.id).key === 'order',
                  }"
                  @click="toggleSort(category.id, 'order')"
                >
                  序号
                  <span class="sort-indicator">
                    {{
                      getSortState(category.id).key === "order"
                        ? getSortState(category.id).order === "asc"
                          ? "↑"
                          : "↓"
                        : ""
                    }}
                  </span>
                </th>
                <th>选手</th>
                <th>学院</th>
                <th
                  class="col-score sortable"
                  :class="{
                    active: getSortState(category.id).key === 'score',
                  }"
                  @click="toggleSort(category.id, 'score')"
                >
                  统计总分
                  <span class="sort-indicator">
                    {{
                      getSortState(category.id).key === "score"
                        ? getSortState(category.id).order === "asc"
                          ? "↑"
                          : "↓"
                        : ""
                    }}
                  </span>
                </th>
                <th class="col-score">统计平均分</th>
                <th class="col-score">原始总分</th>
                <th class="col-score">原始平均分</th>
                <th class="col-dropped">去掉最低分</th>
                <th class="col-dropped">去掉最高分</th>
                <th class="col-count">评委数</th>
              </tr>
            </thead>
            <tbody>
              <template v-if="category.mode === 'vote'">
                <tr
                  v-for="participant in getSortedParticipants(category)"
                  :key="participant.id"
                  :class="{
                    'top-three':
                      (getParticipantRank(category.id, participant.id) || 0) <=
                        3 &&
                      getParticipantRank(category.id, participant.id) !== null,
                  }"
                >
                  <td class="col-rank">
                    <span
                      v-if="getParticipantRank(category.id, participant.id)"
                      class="rank-badge"
                      :class="{
                        gold:
                          getParticipantRank(category.id, participant.id) === 1,
                        silver:
                          getParticipantRank(category.id, participant.id) === 2,
                        bronze:
                          getParticipantRank(category.id, participant.id) === 3,
                      }"
                      >{{
                        getParticipantRank(category.id, participant.id)
                      }}</span
                    >
                    <span v-else class="rank-badge">-</span>
                  </td>
                  <td class="col-order">{{ participant.order || "-" }}</td>
                  <td>
                    <strong>{{ participant.name }}</strong>
                  </td>
                  <td>{{ participant.college || "-" }}</td>
                  <td class="col-score">
                    <span
                      v-if="getParticipantStat(category.id, participant.id)"
                      class="score-highlight"
                      >{{
                        getParticipantStat(category.id, participant.id)
                          ?.vote_count
                      }}</span
                    >
                    <span v-else>-</span>
                  </td>
                  <td class="col-score">
                    <span
                      v-if="getParticipantStat(category.id, participant.id)"
                      >{{
                        props.ctx.getParticipantVoteRate(
                          category.id,
                          participant.id,
                        )
                      }}</span
                    >
                    <span v-else>-</span>
                  </td>
                </tr>
              </template>
              <template v-else>
                <tr
                  v-for="participant in getSortedParticipants(category)"
                  :key="participant.id"
                  :class="{
                    'top-three':
                      (getParticipantRank(category.id, participant.id) || 0) <=
                        3 &&
                      getParticipantRank(category.id, participant.id) !== null,
                  }"
                >
                  <td class="col-rank">
                    <span
                      v-if="getParticipantRank(category.id, participant.id)"
                      class="rank-badge"
                      :class="{
                        gold:
                          getParticipantRank(category.id, participant.id) === 1,
                        silver:
                          getParticipantRank(category.id, participant.id) === 2,
                        bronze:
                          getParticipantRank(category.id, participant.id) === 3,
                      }"
                      >{{
                        getParticipantRank(category.id, participant.id)
                      }}</span
                    >
                    <span v-else class="rank-badge">-</span>
                  </td>
                  <td class="col-order">{{ participant.order || "-" }}</td>
                  <td>
                    <strong>{{ participant.name }}</strong>
                  </td>
                  <td>{{ participant.college || "-" }}</td>
                  <td class="col-score">
                    <span
                      v-if="getParticipantStat(category.id, participant.id)"
                      class="score-highlight"
                      >{{
                        getParticipantStat(category.id, participant.id)?.total
                      }}</span
                    >
                    <span v-else>-</span>
                  </td>
                  <td class="col-score">
                    <span
                      v-if="getParticipantStat(category.id, participant.id)"
                      >{{
                        getParticipantStat(category.id, participant.id)?.average
                      }}</span
                    >
                    <span v-else>-</span>
                  </td>
                  <td class="col-score">
                    <span
                      v-if="getParticipantStat(category.id, participant.id)"
                      >{{
                        getParticipantStat(category.id, participant.id)
                          ?.raw_total
                      }}</span
                    >
                    <span v-else>-</span>
                  </td>
                  <td class="col-score">
                    <span
                      v-if="getParticipantStat(category.id, participant.id)"
                      >{{
                        getParticipantStat(category.id, participant.id)
                          ?.raw_average
                      }}</span
                    >
                    <span v-else>-</span>
                  </td>
                  <td class="col-dropped">
                    {{
                      formatDroppedScores(
                        getParticipantStat(category.id, participant.id),
                        "dropped_lows",
                      )
                    }}
                  </td>
                  <td class="col-dropped">
                    {{
                      formatDroppedScores(
                        getParticipantStat(category.id, participant.id),
                        "dropped_highs",
                      )
                    }}
                  </td>
                  <td class="col-count">
                    <span v-if="getParticipantStat(category.id, participant.id)"
                      >{{
                        getJudgeCountText(
                          category.id,
                          getParticipantStat(category.id, participant.id),
                        )
                      }}</span
                    >
                    <span v-else>-</span>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </div>
    </template>
    <div v-else class="section empty-state">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <path d="M12 20V10 M18 20V4 M6 20v-4" />
      </svg>
      <p>点击"刷新"加载统计数据</p>
    </div>
  </div>
</template>

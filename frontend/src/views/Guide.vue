<template>
  <div class="guide-page">
    <div class="page-header">
      <h1>📖 PRRC 使用手册</h1>
      <p class="subtitle">评审前风险自检系统 — 快速上手指南</p>
    </div>

    <!-- 目录 -->
    <el-card class="toc-card" shadow="never">
      <div class="toctitle">目录</div>
      <ul class="toc-list">
        <li><a href="#overview">🏠 系统简介</a></li>
        <li><a href="#login">🔐 登录与账号</a></li>
        <li><a href="#developer">👨‍💻 开发者操作流程</a></li>
        <li><a href="#reviewer">✅ 评审审核流程</a></li>
        <li><a href="#admin">⚙️ 管理员功能</a></li>
        <li><a href="#faq">❓ 常见问题</a></li>
      </ul>
    </el-card>

    <!-- 系统简介 -->
    <el-card id="overview" class="section-card">
      <template #header>
        <div class="section-title">🏠 系统简介</div>
      </template>
      <p>PRRC（评审前风险自检系统）用于在代码合入前，对固件变更进行系统性风险自检，确保关键模块经过充分测试。</p>
      <el-divider />
      <h4>核心概念</h4>
      <ul class="concept-list">
        <li><strong>风险模块</strong> — 将固件按功能域划分（如 Bootloader/启动链、升级流程、参数存储等），每个模块有不同的风险等级（HIGH / MEDIUM / LOW）。</li>
        <li><strong>测试项</strong> — 每个模块下配置的标准测试用例（如"正常升级"、"掉电恢复"等），测试项直接归属模块，无需额外映射配置。</li>
        <li><strong>自检单</strong> — 一次变更对应一张自检单，包含：变更信息、所选模块、系统生成的测试项列表。</li>
        <li><strong>编号规则</strong> — 提交后自动生成，格式为 <code>PRRC-YYYYMMDD-XXXX</code>，如 <code>PRRC-20260518-0001</code>。</li>
      </ul>
      <el-divider />
      <h4>风险等级说明</h4>
      <div class="risk-grid">
        <div class="risk-item risk-HIGH">🔴 HIGH — 高风险</div>
        <div class="risk-item risk-MEDIUM">🟡 MEDIUM — 中风险</div>
        <div class="risk-item risk-LOW">🟢 LOW — 低风险</div>
      </div>
      <p style="margin-top:8px">自检单的风险等级由所选模块中最高等级决定（如选了任何一个 HIGH 模块，整张单为 HIGH）。</p>
    </el-card>

    <!-- 登录与账号 -->
    <el-card id="login" class="section-card">
      <template #header>
        <div class="section-title">🔐 登录与账号</div>
      </template>
      <h4>登录步骤</h4>
      <el-steps :active="3" align-center finish-status="success">
        <el-step title="打开系统" description="访问系统 URL" />
        <el-step title="输入账号密码" description="使用分配的账号登录" />
        <el-step title="进入首页" description="查看自检单列表" />
      </el-steps>
      <el-divider />
      <h4>角色说明</h4>
      <el-table :data="roleTableData" stripe style="width:100%">
        <el-table-column prop="role" label="角色" width="120" />
        <el-table-column prop="desc" label="说明" />
        <el-table-column prop="rights" label="权限" />
      </el-table>
      <el-divider />
      <h4>测试账号（初始化数据）</h4>
      <el-table :data="accountTableData" stripe style="width:100%">
        <el-table-column prop="user" label="用户名" width="140" />
        <el-table-column prop="pass" label="密码" width="140" />
        <el-table-column prop="role" label="角色" width="100" />
        <el-table-column prop="name" label="姓名" />
      </el-table>
    </el-card>

    <!-- 开发者流程 -->
    <el-card id="developer" class="section-card">
      <template #header>
        <div class="section-title">👨‍💻 开发者操作流程</div>
      </template>

      <el-steps :active="5" align-center style="margin-bottom:24px">
        <el-step title="创建自检单" />
        <el-step title="填写变更信息" />
        <el-step title="选择风险模块" />
        <el-step title="填写测试结果" />
        <el-step title="提交" />
      </el-steps>

      <el-collapse v-model="devSteps" accordion>
        <el-collapse-item title="步骤一：创建自检单" name="1">
          <div class="step-content">
            <p>点击左侧菜单 <strong>「自检单」</strong>，进入自检单列表页。点击右上角 <el-button type="primary" size="small">新建自检单</el-button> 按钮。</p>
            <el-alert type="info" :closable="false" show-icon style="margin:12px 0">
              每张自检单对应一次固件变更，建议一个 MR/PR 对应一张自检单。
            </el-alert>
          </div>
        </el-collapse-item>

        <el-collapse-item title="步骤二：填写变更信息" name="2">
          <div class="step-content">
            <p>在编辑页面填写以下字段：</p>
            <ul>
              <li><strong>变更标题</strong> — 简洁描述本次变更，如"修复升级中断恢复问题"</li>
              <li><strong>关联项目</strong> — 从下拉列表选择（储能逆变器/并网逆变器/户用光伏）</li>
              <li><strong>产品型号</strong> — 输入具体型号，如 ES-100K</li>
              <li><strong>版本号</strong> — 本次变更涉及的固件版本，如 V1.2.3</li>
              <li><strong>变更类型</strong> — BUGFIX / FEATURE / OPTIMIZATION / OTHER</li>
              <li><strong>变更概述</strong> — 详细说明本次变更内容和目的</li>
              <li><strong>分支名称</strong> — Git 分支名，如 feature/upgrade-fix</li>
              <li><strong>MR/PR 链接</strong> — 代码合并请求地址（选填）</li>
            </ul>
          </div>
        </el-collapse-item>

        <el-collapse-item title="步骤三：选择风险模块" name="3">
          <div class="step-content">
            <p>勾选本次变更涉及的风险模块。系统会根据选择自动生成对应的测试项。</p>
            <el-alert type="warning" :closable="false" show-icon style="margin:12px 0">
              请准确选择模块，避免遗漏。选错模块会导致测试项不完整，影响评审结果。
            </el-alert>
            <p><strong>示例场景：</strong></p>
            <ul>
              <li>只改了参数存储逻辑 → 勾选「参数存储」</li>
              <li>改了升级流程 + 参数存储 → 勾选「升级流程」+「参数存储」</li>
              <li>涉及状态机调度 → 勾选「状态机/调度/看门狗」</li>
            </ul>
          </div>
        </el-collapse-item>

        <el-collapse-item title="步骤四：填写测试结果" name="4">
          <div class="step-content">
            <p>系统根据所选模块生成测试项列表，逐项填写：</p>
            <ul>
              <li><strong>是否执行</strong> — YES（已测试）/ NO（未测试）/ NA（不适用）</li>
              <li><strong>测试结果</strong> — PASS / FAIL（仅执行了才需要填）</li>
              <li><strong>备注说明</strong> — 未执行或不通过时必须填写原因</li>
            </ul>
            <el-alert type="info" :closable="false" show-icon style="margin:12px 0">
              必做项（标记为「必做」）必须执行并填写结果，否则无法提交。
            </el-alert>
            <p><strong>示例：</strong></p>
            <el-table :data="testResultExample" stripe size="small">
              <el-table-column prop="item" label="测试项" />
              <el-table-column prop="executed" label="是否执行" width="100" />
              <el-table-column prop="result" label="结果" width="80" />
              <el-table-column prop="remark" label="备注" />
            </el-table>
          </div>
        </el-collapse-item>

        <el-collapse-item title="步骤五：提交自检单" name="5">
          <div class="step-content">
            <p>所有必做项填写完毕后，点击 <el-button type="primary" size="small">提交自检单</el-button>。</p>
            <p>提交后：</p>
            <ul>
              <li>系统生成唯一编号，如 <code>PRRC-20260518-0001</code></li>
              <li>状态变为「已提交」</li>
              <li>等待评审人员审核</li>
            </ul>
            <el-alert type="success" :closable="false" show-icon style="margin:12px 0">
              提交后如需修改，可以申请退回。退回后状态变为「已退回」，修改后可重新提交。
            </el-alert>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <!-- 评审流程 -->
    <el-card id="reviewer" class="section-card">
      <template #header>
        <div class="section-title">✅ 评审审核流程</div>
      </template>
      <p>评审人员登录后，可在「自检单列表」中看到所有状态为「已提交」的自检单。</p>
      <el-divider />
      <h4>审核操作</h4>
      <el-steps :active="2" align-center finish-status="success">
        <el-step title="查看详情" description="点击自检单查看变更信息和测试结果" />
        <el-step title="给出结论" description="通过 / 退回修改" />
      </el-steps>
      <el-divider />
      <h4>审核结论</h4>
      <ul>
        <li><strong>✅ 通过（APPROVED）</strong> — 自检单通过评审，可以合入代码。</li>
        <li><strong>🔄 退回修改（RETURNED）</strong> — 测试项不全或有问题，退回给开发者补充。开发者修改后可重新提交。</li>
      </ul>
      <el-divider />
      <h4>评审要点</h4>
      <ul>
        <li>检查变更描述是否清晰</li>
        <li>确认所选模块是否覆盖了实际改动的功能域</li>
        <li>验证 HIGH 风险模块是否都有对应测试</li>
        <li>检查必做项是否全部执行并通过</li>
        <li>FAIL 的测试项是否有合理的说明</li>
      </ul>
    </el-card>

    <!-- 管理员功能 -->
    <el-card id="admin" class="section-card">
      <template #header>
        <div class="section-title">⚙️ 管理员功能</div>
      </template>
      <p>管理员可访问「系统管理」菜单，对项目、风险模块、测试项、用户等进行维护。</p>
      <el-divider />

      <h4>项目管理</h4>
      <p>管理系统支持的产品项目，如储能逆变器、并网逆变器等。每个项目可设置默认产品型号。</p>
      <el-divider />

      <h4>风险模块管理 <span style="font-weight:normal;color:#888;font-size:13px">（含测试项）</span></h4>
      <p>管理固件风险模块。点开模块左侧的 <strong>▶</strong> 展开按钮，可直接在该模块下新增、编辑、删除测试项。</p>
      <p>每个测试项包含以下字段：</p>
      <ul>
        <li><strong>模块</strong> — 测试项归属的模块（下拉选择）</li>
        <li><strong>测试名称</strong> — 中文名称，如「正常启动」</li>
        <li><strong>测试编码</strong> — 唯一英文标识，如 BOOT_NORMAL</li>
        <li><strong>必做</strong> — 开关，ON = 提交时必须执行并填写结果</li>
        <li><strong>风险等级</strong> — HIGH / MEDIUM / LOW</li>
        <li><strong>描述</strong> — 测试项的详细说明</li>
      </ul>
      <el-alert type="info" :closable="false" show-icon style="margin:12px 0">
        测试项直接归属模块，无需额外配置映射关系，结构更简洁。
      </el-alert>
      <el-divider />

      <h4>测试项管理</h4>
      <p>以列表形式统一管理所有测试项，可按模块筛选、搜索、编辑和删除。</p>
      <el-divider />

      <h4>用户管理</h4>
      <p>管理系统用户账号，设置角色（管理员/评审/开发者）。</p>
      <el-divider />

      <h4>操作日志</h4>
      <p>记录所有用户在系统中的操作行为，包括操作人、操作类型、业务对象和详情。</p>
    </el-card>

    <!-- 常见问题 -->
    <el-card id="faq" class="section-card">
      <template #header>
        <div class="section-title">❓ 常见问题</div>
      </template>
      <el-collapse v-model="faqOpen">
        <el-collapse-item title='Q: 提交时提示「必做项未填写」？' name="faq1">
          <p>标记为「必做」的测试项，「是否执行」字段必须填写。如果某项不适用，选择「NA」并填写原因。</p>
        </el-collapse-item>
        <el-collapse-item title='Q: 选错了风险模块怎么办？' name="faq2">
          <p>在「已退回」状态下，可以编辑自检单，重新选择模块并重新填写测试结果，然后重新提交。</p>
        </el-collapse-item>
        <el-collapse-item title='Q: 一个 MR 涉及多个不相关的改动，可以开一张自检单吗？' name="faq3">
          <p>建议按改动域分开建单。例如：同时改了升级流程和 UI 显示，可以建两张自检单，分别关联对应的模块。</p>
        </el-collapse-item>
        <el-collapse-item title="Q: 测试结果为 FAIL 还能提交吗？" name="faq4">
          <p>可以提交，但必须在备注中说明失败原因。评审人员会根据情况判断是否需要修复后重新测试。</p>
        </el-collapse-item>
        <el-collapse-item title="Q: 评审人员可以看到操作记录吗？" name="faq5">
          <p>可以。管理员可在「操作日志」中查看所有用户的操作记录，包括创建、修改、提交、审核等操作。</p>
        </el-collapse-item>
        <el-collapse-item title="Q: 如何添加新的风险模块或测试项？" name="faq6">
          <p>由管理员在「系统管理 → 风险模块」中添加。点开模块左侧的 ▶ 展开按钮，点击「新增测试项」即可在该模块下直接添加测试项。</p>
        </el-collapse-item>
        <el-collapse-item title="Q: 忘记了密码怎么办？" name="faq7">
          <p>请联系系统管理员重置密码。管理员可在「用户管理」中找到对应用户进行密码重置。</p>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <div class="page-footer">
      <p>如有更多问题，请联系系统管理员或开发团队。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"

const devSteps = ref("1")
const faqOpen = ref("faq1")

const roleTableData = [
  { role: "管理员", desc: "系统维护人员", rights: "全部功能（用户/模块/测试项管理）" },
  { role: "评审", desc: "代码评审人员", rights: "审核自检单、查看所有记录" },
  { role: "开发者", desc: "固件开发人员", rights: "创建/填写/提交自检单" },
]

const accountTableData = [
  { user: "admin", pass: "Admin@123", role: "管理员", name: "管理员" },
  { user: "dev1", pass: "Dev@123", role: "开发者", name: "开发一" },
  { user: "dev2", pass: "Dev@123", role: "开发者", name: "开发二" },
  { user: "review1", pass: "Review@123", role: "评审", name: "评审一" },
  { user: "review2", pass: "Review@123", role: "评审", name: "评审二" },
  { user: "tester1", pass: "Test@123", role: "测试", name: "测试一" },
]

const testResultExample = [
  { item: "正常升级", executed: "YES", result: "PASS", remark: "本地验证通过" },
  { item: "升级中断恢复", executed: "YES", result: "PASS", remark: "掉电测试 10 次均正常恢复" },
  { item: "参数保存", executed: "YES", result: "PASS", remark: "重启后参数保持正确" },
  { item: "UI 显示", executed: "NA", result: "—", remark: "本次改动不涉及 UI 模块" },
]
</script>

<style scoped>
.guide-page {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 28px;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.subtitle { color: #666; font-size: 14px; }

.toc-card { margin-bottom: 20px; background: #f8f9ff; border: 1px solid #e0e7ff; }
.toctitle { font-size: 16px; font-weight: 600; color: #333; margin-bottom: 12px; }
.toc-list { list-style: none; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.toc-list a { color: #409eff; text-decoration: none; font-size: 14px; padding: 4px 8px; border-radius: 4px; display: block; transition: background 0.2s; }
.toc-list a:hover { background: #e0e7ff; }

.section-card { margin-bottom: 20px; }
.section-title { font-size: 16px; font-weight: 600; color: #1a1a2e; }
.section-card h4 { color: #333; margin-bottom: 10px; font-size: 15px; }
.section-card ul { padding-left: 20px; line-height: 1.8; color: #555; }
.section-card ul li { margin-bottom: 4px; }
.section-card p { line-height: 1.7; color: #555; }
.concept-list li { margin-bottom: 10px !important; }

.risk-grid { display: flex; gap: 16px; margin-bottom: 8px; }
.risk-item { padding: 8px 16px; border-radius: 6px; font-size: 14px; font-weight: 500; }
.risk-item.risk-HIGH { background: #fee2e2; color: #991b1b; }
.risk-item.risk-MEDIUM { background: #fef9c3; color: #854d0e; }
.risk-item.risk-LOW { background: #dcfce7; color: #166534; }

.step-content { padding: 4px 0; }
.step-content ul { margin-top: 10px; }

.page-footer { text-align: center; color: #999; font-size: 13px; padding: 20px 0; border-top: 1px solid #eee; margin-top: 20px; }

code {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 13px;
  color: #c7254e;
}
</style>

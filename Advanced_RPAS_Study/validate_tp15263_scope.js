const fs = require("fs");
const path = require("path");

const root = __dirname;
const questionPath = path.join(root, "data", "questions.json");
const data = JSON.parse(fs.readFileSync(questionPath, "utf8"));
const questions = data.questions || [];

const level1Pattern = /\b(BVLOS|beyond visual line[- ]of[- ]sight|Level 1 Complex|TP\s*15530|detect[- ]and[- ]avoid|\bDAA\b)\b/i;
const tp15263Pattern = /\bTP\s*15263\b/i;
const allowedScopes = new Set([
  "core-basic-advanced",
  "core-advanced",
  "supplemental",
  "level-1-complex",
]);
const allowedLevels = new Set([
  "basic",
  "advanced",
  "basic-advanced",
  "supplemental",
  "level-1-complex",
  "level 1 complex",
]);

function joinedQuestionText(question) {
  return [
    question.id,
    question.question,
    question.rationale,
    question.source,
    question.examScope,
    question.examLevel,
    question.tp15263Section,
    question.knowledgeArea,
    question.knowledgeTopic,
    question.learningObjective,
    ...(question.sourceRefs || []),
  ]
    .filter(Boolean)
    .join(" ");
}

function bucketBy(field) {
  return questions.reduce((acc, question) => {
    const key = question[field] || "(blank)";
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});
}

const issues = [];
const defaultPool = questions.filter((question) =>
  ["core-basic-advanced", "core-advanced"].includes(question.examScope)
);

for (const question of questions) {
  const text = joinedQuestionText(question);

  if (!question.examScope) {
    issues.push({ severity: "info", id: question.id, issue: "Missing examScope" });
  } else if (!allowedScopes.has(question.examScope)) {
    issues.push({ severity: "error", id: question.id, issue: `Unexpected examScope '${question.examScope}'` });
  }

  const examLevel = question.examLevel ? String(question.examLevel).toLowerCase() : "";
  if (!question.examLevel) {
    issues.push({ severity: "info", id: question.id, issue: "Missing examLevel" });
  } else if (!allowedLevels.has(examLevel)) {
    issues.push({ severity: "error", id: question.id, issue: `Unexpected examLevel '${question.examLevel}'` });
  }

  if (["core-basic-advanced", "core-advanced"].includes(question.examScope) && level1Pattern.test(text)) {
    issues.push({ severity: "error", id: question.id, issue: "Default pool contains Level 1 Complex/BVLOS/TP 15530 language" });
  }

  if (question.examScope === "level-1-complex" && tp15263Pattern.test(text) && !level1Pattern.test(text)) {
    issues.push({ severity: "warn", id: question.id, issue: "Level 1 Complex scope references TP 15263 without an obvious Level 1/BVLOS term" });
  }
}

const sectionCounts = {};
for (const question of defaultPool) {
  const section = question.tp15263Section || "(blank)";
  sectionCounts[section] = (sectionCounts[section] || 0) + 1;
}

console.log("TP 15263 Scope Validation");
console.log("=========================");
console.log(`Total questions: ${questions.length}`);
console.log(`Default Basic/Advanced pool: ${defaultPool.length}`);
console.log("");
console.log("examScope:", JSON.stringify(bucketBy("examScope"), null, 2));
console.log("examLevel:", JSON.stringify(bucketBy("examLevel"), null, 2));
console.log("Default pool by tp15263Section:", JSON.stringify(sectionCounts, null, 2));
console.log("");

const bySeverity = issues.reduce((acc, issue) => {
  acc[issue.severity] = (acc[issue.severity] || 0) + 1;
  return acc;
}, {});
console.log("Issues:", JSON.stringify(bySeverity, null, 2));

for (const issue of issues.sort((a, b) => a.severity.localeCompare(b.severity)).slice(0, 80)) {
  console.log(`[${issue.severity}] ${issue.id}: ${issue.issue}`);
}

if (issues.length > 80) {
  console.log(`... ${issues.length - 80} more issues omitted`);
}

if ((bySeverity.error || 0) > 0) {
  process.exitCode = 1;
}

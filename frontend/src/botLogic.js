import { courses } from "./data/courseData";
import { students } from "./data/studentData";
import { users } from "./data/userData";

let currentUser = null;

export function getBotReply(input) {
  const question = input.toLowerCase().replace(/\s+/g, "");
  // Verify User ID
const userIdMatch = input.match(/(?:user|student|officer|lecturer)\s*id\s*:?\s*([SOL]\d+)/i);

if (userIdMatch) {
  const userId = userIdMatch[1].toUpperCase();

  const user = users.find(
    (item) => item.userId.toUpperCase() === userId
  );

  if (!user) {
    currentUser = null;
    return `I could not verify User ID ${userId} in the available trusted university data. Access denied.`;
  }

  if (!user.authorized) {
    currentUser = null;
    return `User ID ${userId} was found, but this ${user.role} is not currently authorized. Access denied.`;
  }

  currentUser = user;

  return `Identity verified. ${user.name} is an authorized ${user.role}. You may now use the chatbot according to your role permissions.`;
}

// Check current authorization status
if (
  question.includes("whoami") ||
  question.includes("authorizationstatus")
) {
  if (!currentUser) {
    return "No authorized user is currently verified in this session.";
  }

  return `Current user: ${currentUser.userId} (${currentUser.name}), Role: ${currentUser.role}, Authorized: yes.`;
}

// Show role permissions
if (
  question.includes("whatcaniaccess") ||
  question.includes("whatcanido") ||
  question.includes("mypermissions") ||
  question.includes("permissions")
) {
  if (!currentUser) {
    return "Access denied. Please verify your User ID first.";
  }

  if (currentUser.role === "student") {
    return "As a student, you can access your own credit mapping information only. You are not authorized to access another student's personal information.";
  }

  if (currentUser.role === "lecturer") {
    return "As a lecturer, you can review student credit mapping information and mapping evidence. You cannot modify, approve, or override mapping decisions.";
  }

  if (currentUser.role === "officer") {
    return "As an officer, you can review student credit mappings, mapping evidence, and administrative review information. Higher-level approval or override actions can be handled according to officer permissions.";
  }

  return "Your role does not currently have defined permissions.";
}

// Logout / end authorized session
if (
  question.includes("logout") ||
  question.includes("signout")
) {
  if (!currentUser) {
    return "There is no authorized user session to end.";
  }

  const userName = currentUser.name;

  currentUser = null;

  return `${userName} has been signed out. Authorization has been cleared.`;
}

    // Search by Student ID
const studentIdMatch = input.match(/student\s*id\s*:?\s*(\d+)/i);

if (studentIdMatch) {
  const studentId = studentIdMatch[1];

  // No verified user
  if (!currentUser) {
    return "Access denied. Please verify your User ID before accessing student information.";
  }

  // Student role: can only access their own information
  if (
    currentUser.role === "student" &&
    currentUser.studentId !== studentId
  ) {
    currentUser = null;

    return "Access denied. Students are not authorized to access another student's personal information. This session has been ended.";
  }

  // Student / Officer / Lecturer can access according to role
  const allowedRoles = ["student", "officer", "lecturer"];

  if (!allowedRoles.includes(currentUser.role)) {
    return "Access denied. Your role is not authorized to access student credit mapping information.";
  }

  // Search for the student
  const student = students.find(
    (item) => item.studentId === studentId
  );

  // Student does not exist
  if (!student) {
    return `I could not find Student ID ${studentId} in the available trusted university data.`;
  }

  // Student exists but has no mappings
  if (
    !student.creditMappings ||
    student.creditMappings.length === 0
  ) {
    return `Student ID ${studentId} was found, but there are no credit mappings available for this student.`;
  }

  // Format mapping records
  const mappings = student.creditMappings
    .map(
      (mapping) =>
        `${mapping.sourceCourseCode} - ${mapping.sourceCourseTitle} → ${mapping.targetCourseCode} - ${mapping.targetCourseTitle} (Status: ${mapping.status})`
    )
    .join("\n");

  return `Student ID ${studentId} has the following credit mappings:\n${mappings}`;
}


// Check course equivalence / mapping questions
const courseCodes = input.match(/[A-Za-z]{4}\s*\d{4,6}[A-Za-z]?/g);

if (
  courseCodes &&
  courseCodes.length >= 2 &&
  (question.includes("equivalent") ||
    question.includes("mapping") ||
    question.includes("credit"))
) {
  const normalizedCodes = courseCodes.map((code) =>
    code.replace(/\s+/g, "").toUpperCase()
  );

  const [firstCode, secondCode] = normalizedCodes;

  const knownMapping = students
    .flatMap((student) => student.creditMappings)
    .find(
      (mapping) =>
        (mapping.sourceCourseCode.toUpperCase() === firstCode &&
          mapping.targetCourseCode.toUpperCase() === secondCode) ||
        (mapping.sourceCourseCode.toUpperCase() === secondCode &&
          mapping.targetCourseCode.toUpperCase() === firstCode)
    );

  if (knownMapping) {
    return `A trusted credit mapping record was found: ${knownMapping.sourceCourseCode} - ${knownMapping.sourceCourseTitle} → ${knownMapping.targetCourseCode} - ${knownMapping.targetCourseTitle}. Status: ${knownMapping.status}.`;
  }

  return `I found the course codes ${firstCode} and ${secondCode}, but I could not find a trusted credit mapping record connecting these courses. I cannot confirm that they are equivalent.`;
}

  // Search by course code
  const course = courses.find((item) =>
    question.includes(item.code.toLowerCase())
  );

  if (course) {
    return `${course.code} is ${course.title}. ${course.description}`;
  }

  // Search by course topic
  const topicMatch = courses.find((item) =>
    item.keywords.some((keyword) =>
      input.toLowerCase().includes(keyword.toLowerCase())
    )
  );

  if (topicMatch) {
    return `A relevant Adelaide University course is ${topicMatch.code} - ${topicMatch.title}. ${topicMatch.description}`;
  }

  if (
    question.includes("hello") ||
    question.includes("hi")
  ) {
    return "Hi! How can I help you with course mapping today?";
  }

  if (question.includes("evidence")) {
    return "Course mapping evidence can include learning outcomes, course descriptions, syllabus content, assessment information and credit weighting.";
  }

  if (question.includes("confidence")) {
    return "The confidence score indicates how strongly the available evidence supports a suggested course equivalency. Final approval remains with the reviewer.";
  }

  return "I do not have enough information in the available trusted university data to answer this question. I can only provide information supported by the available course, student, and credit mapping data.";
}
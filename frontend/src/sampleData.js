const mixedLines = [
  "name,email",
  "Aarav Sharma,aarav@example.com",
  ",missing.name@example.com", // fails: name is required
  "Bad Email Person,not-an-email", // fails: invalid email
  "Priya Nair,priya@example.com",
  "Priya Nair,priya@example.com", // duplicate: allowed, gets its own file
  "Z".repeat(150) + ",toolong@example.com", // fails: name over 100 characters
  "Dr. Venkata Subrahmanyam Raghavendra Chandrasekhar Iyer,venkat@example.com", // long but valid: font shrinks
  "Meera Patel,meera@example.com",
];

const validLines = [
  "name,email",
  "Asha Rao,asha@example.com",
  "Rohan Mehta,rohan@example.com",
  "Kavya Iyer,kavya@example.com",
  "Neel Shah,neel@example.com",
  "Sara Thomas,sara@example.com",
];

const failureLines = [
  "name,email",
  ",missing-name@example.com",
  "Invalid Email,not-an-email",
  "Another Invalid Email,missing-at.example.com",
  "Valid Recipient,valid@example.com",
];

export const SAMPLE_DATASETS = [
  {
    id: "mixed",
    label: "Mixed valid and invalid rows",
    eventName: "Introduction to Machine Learning",
    issuerName: "Tech Club",
    csv: mixedLines.join("\n"),
  },
  {
    id: "valid",
    label: "All valid recipients",
    eventName: "Frontend Development Workshop",
    issuerName: "Engineering Academy",
    csv: validLines.join("\n"),
  },
  {
    id: "failures",
    label: "Failure handling demo",
    eventName: "Data Quality Review",
    issuerName: "Training Team",
    csv: failureLines.join("\n"),
  },
];

export const SAMPLE_CSV = SAMPLE_DATASETS[0].csv;

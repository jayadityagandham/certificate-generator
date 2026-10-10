// Sample recipients that deliberately include bad rows, so a reviewer can see
// failed certificates being isolated from the good ones in one click.
const lines = [
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

export const SAMPLE_CSV = lines.join("\n");

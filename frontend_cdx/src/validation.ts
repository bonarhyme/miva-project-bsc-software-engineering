export const REG_NUMBER_PATTERN = "\\d{4}/[A-Za-z]{3,4}/[A-Za-z]/\\d{4,5}";
export const COURSE_ID_PATTERN = "[A-Za-z]{3,4}-\\d{3}";

export const regNumberRegex = new RegExp(`^${REG_NUMBER_PATTERN}$`);
export const courseIdRegex = new RegExp(`^${COURSE_ID_PATTERN}$`);

export function isValidEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
}

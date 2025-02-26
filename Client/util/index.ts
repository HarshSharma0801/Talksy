import { format, subHours, isBefore } from "date-fns";

export const timeConvert = (timestamp: string | Date): string => {
  const now = new Date();
  const twentyFourHoursAgo = subHours(now, 24);

  const parsedTimestamp =
    timestamp instanceof Date 
      ? new Date(timestamp.getTime() + timestamp.getTimezoneOffset() * 60000) 
      : new Date(new Date(timestamp).getTime() + new Date(timestamp).getTimezoneOffset() * 60000);

  if (isBefore(parsedTimestamp, twentyFourHoursAgo)) {
    return format(parsedTimestamp, "d MMM yyyy");
  } else {
    return format(parsedTimestamp, "HH:mm");
  }
};
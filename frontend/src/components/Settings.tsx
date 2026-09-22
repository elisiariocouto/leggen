import SyncScheduleCard from "./settings/SyncScheduleCard";
import NotificationServicesCard from "./settings/NotificationServicesCard";
import NotificationFiltersCard from "./settings/NotificationFiltersCard";
import BackupCard from "./settings/BackupCard";

export default function Settings() {
  return (
    <div className="space-y-6">
      <SyncScheduleCard />
      <NotificationServicesCard />
      <NotificationFiltersCard />
      <BackupCard />
    </div>
  );
}

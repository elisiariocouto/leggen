import { Filter } from "lucide-react";
import { useNotificationSettings } from "../../hooks/queries";
import { CardContent } from "../ui/card";
import { Label } from "../ui/label";
import SettingsCard from "./SettingsCard";
import NotificationFiltersDrawer from "./NotificationFiltersDrawer";

function FilterTerms({ label, terms }: { label: string; terms?: string[] | null }) {
  return (
    <div>
      <Label className="text-xs font-medium text-muted-foreground mb-2 block">
        {label}
      </Label>
      <div className="min-h-8 flex flex-wrap gap-1">
        {terms && terms.length > 0 ? (
          terms.map((term) => (
            <span
              key={term}
              className="inline-flex items-center px-2 py-1 bg-secondary text-secondary-foreground rounded text-xs"
            >
              {term}
            </span>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">None</p>
        )}
      </div>
    </div>
  );
}

export default function NotificationFiltersCard() {
  const query = useNotificationSettings();

  return (
    <SettingsCard
      icon={Filter}
      title="Notification Filters"
      action={<NotificationFiltersDrawer settings={query.data} />}
      query={query}
    >
      {(settings) => (
        <CardContent>
          {settings.filters ? (
            <div className="space-y-4">
              <div className="bg-muted rounded-md p-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <FilterTerms
                    label="Case Insensitive Filters"
                    terms={settings.filters.case_insensitive}
                  />
                  <FilterTerms
                    label="Case Sensitive Filters"
                    terms={settings.filters.case_sensitive}
                  />
                </div>
              </div>
              <p className="text-sm text-muted-foreground">
                Filters determine which transaction descriptions will trigger
                notifications. Add terms to exclude transactions containing
                those words.
              </p>
            </div>
          ) : (
            <div className="text-center py-8">
              <Filter className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">
                No notification filters configured
              </h3>
              <p className="text-muted-foreground">
                Set up filters to control which transactions trigger
                notifications.
              </p>
            </div>
          )}
        </CardContent>
      )}
    </SettingsCard>
  );
}

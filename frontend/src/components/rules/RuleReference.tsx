import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";
import { Skeleton } from "@/components/ui/skeleton";
import type { RuleReference as RuleReferenceData } from "@/types/api";

/**
 * The scripting reference, fetched from the server so it always describes
 * the runtime this leggen actually has.
 */
export default function RuleReference({
  onUseExample,
}: {
  onUseExample?: (script: string) => void;
}) {
  const { data, isLoading } = useQuery<RuleReferenceData>({
    queryKey: queryKeys.ruleReference,
    queryFn: apiClient.getRuleReference,
    staleTime: Infinity,
  });

  if (isLoading || !data) {
    return (
      <div className="space-y-2">
        {[...Array(6)].map((_, i) => (
          <Skeleton key={i} className="h-5 w-full" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-5 text-sm">
      <section>
        <h4 className="mb-2 font-medium">How a rule works</h4>
        <ul className="list-disc space-y-1 pl-5 text-muted-foreground">
          {data.notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      </section>

      {data.fields.map((group) => (
        <section key={group.title}>
          <h4 className="mb-2 font-medium">{group.title}</h4>
          <dl className="space-y-1.5">
            {group.fields.map((field) => (
              <div key={field.name}>
                <dt className="font-mono text-xs">
                  {field.name}{" "}
                  <span className="font-sans text-muted-foreground">
                    {field.type}
                  </span>
                </dt>
                <dd className="text-xs text-muted-foreground">
                  {field.description}
                </dd>
              </div>
            ))}
          </dl>
        </section>
      ))}

      {data.stdlib.map((group) => (
        <section key={group.title}>
          <h4 className="mb-2 font-medium">{group.title}</h4>
          <dl className="space-y-1.5">
            {group.functions.map((fn) => (
              <div key={fn.signature}>
                <dt className="font-mono text-xs">{fn.signature}</dt>
                <dd className="text-xs text-muted-foreground">
                  {fn.description}
                </dd>
              </div>
            ))}
          </dl>
        </section>
      ))}

      {data.examples.length > 0 && (
        <section>
          <h4 className="mb-2 font-medium">Examples</h4>
          <div className="space-y-3">
            {data.examples.map((example) => (
              <div key={String(example.title)}>
                <div className="mb-1 flex items-center justify-between gap-2">
                  <span className="text-xs text-muted-foreground">
                    {String(example.title)}
                  </span>
                  {onUseExample && (
                    <button
                      type="button"
                      className="text-xs text-primary hover:underline"
                      onClick={() => onUseExample(String(example.lua_script))}
                    >
                      Use
                    </button>
                  )}
                </div>
                <pre className="overflow-x-auto rounded-md bg-muted p-2 font-mono text-xs">
                  {String(example.lua_script)}
                </pre>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

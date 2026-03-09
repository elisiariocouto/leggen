import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, Trash2, Tag, EyeOff } from "lucide-react";
import { toast } from "sonner";
import { apiClient } from "../lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog";
import { Switch } from "./ui/switch";
import type { Category } from "../types/api";

const PRESET_COLORS = [
  "#22c55e", "#3b82f6", "#a855f7", "#f97316", "#ec4899",
  "#64748b", "#eab308", "#ef4444", "#06b6d4", "#84cc16",
  "#8b5cf6", "#6b7280", "#14b8a6", "#f43f5e", "#0ea5e9",
];

function CategoryForm({
  category,
  onSave,
  onCancel,
  isSaving,
}: {
  category?: Category;
  onSave: (name: string, color: string, excludeFromStats: boolean) => void;
  onCancel: () => void;
  isSaving: boolean;
}) {
  const [name, setName] = useState(category?.name ?? "");
  const [color, setColor] = useState(category?.color ?? "#6b7280");
  const [excludeFromStats, setExcludeFromStats] = useState(
    category?.exclude_from_stats ?? false
  );

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="category-name">Name</Label>
        <Input
          id="category-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Category name"
        />
      </div>
      <div className="space-y-2">
        <Label>Color</Label>
        <div className="flex flex-wrap gap-2">
          {PRESET_COLORS.map((c) => (
            <button
              key={c}
              className={`h-7 w-7 rounded-full border-2 transition-transform ${
                color === c ? "border-foreground scale-110" : "border-transparent"
              }`}
              style={{ backgroundColor: c }}
              onClick={() => setColor(c)}
              type="button"
            />
          ))}
        </div>
        <div className="flex items-center gap-2 mt-2">
          <Input
            type="color"
            value={color}
            onChange={(e) => setColor(e.target.value)}
            className="h-8 w-14 p-0.5 cursor-pointer"
          />
          <span className="text-xs text-muted-foreground">{color}</span>
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="space-y-0.5">
          <Label htmlFor="exclude-from-stats">Exclude from statistics</Label>
          <p className="text-xs text-muted-foreground">
            Transactions in this category won&apos;t count toward income/expense totals.
          </p>
        </div>
        <Switch
          id="exclude-from-stats"
          checked={excludeFromStats}
          onCheckedChange={setExcludeFromStats}
        />
      </div>
      <div className="flex justify-end gap-2">
        <Button variant="outline" size="sm" onClick={onCancel}>
          Cancel
        </Button>
        <Button
          size="sm"
          onClick={() => onSave(name, color, excludeFromStats)}
          disabled={!name.trim() || isSaving}
        >
          {isSaving ? "Saving..." : category ? "Update" : "Create"}
        </Button>
      </div>
    </div>
  );
}

export default function CategoryManager() {
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Category | null>(null);
  const queryClient = useQueryClient();

  const { data: categories, isLoading } = useQuery<Category[]>({
    queryKey: ["categories"],
    queryFn: apiClient.getCategories,
  });

  const createMutation = useMutation({
    mutationFn: (data: { name: string; color: string; exclude_from_stats: boolean }) =>
      apiClient.createCategory(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      setShowCreate(false);
      toast.success("Category created.");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to create category.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number;
      data: { name: string; color: string; exclude_from_stats: boolean };
    }) => apiClient.updateCategory(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      setEditingCategory(null);
      toast.success("Category updated.");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to update category.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.deleteCategory(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      setDeleteTarget(null);
      toast.success("Category deleted.");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to delete category.");
    },
  });

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <Tag className="h-5 w-5 text-primary" />
            <span>Categories</span>
          </CardTitle>
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                <Plus className="h-4 w-4 mr-1" />
                New
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Category</DialogTitle>
                <DialogDescription>
                  Add a new category for organizing transactions.
                </DialogDescription>
              </DialogHeader>
              <CategoryForm
                onSave={(name, color, excludeFromStats) =>
                  createMutation.mutate({
                    name,
                    color,
                    exclude_from_stats: excludeFromStats,
                  })
                }
                onCancel={() => setShowCreate(false)}
                isSaving={createMutation.isPending}
              />
            </DialogContent>
          </Dialog>
        </div>
        <CardDescription>
          Manage transaction categories used for organizing and tracking spending.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="text-sm text-muted-foreground">Loading categories...</div>
        ) : (
          <div className="space-y-2">
            {categories?.map((cat) => (
              <div
                key={cat.id}
                className="flex items-center justify-between p-2 rounded-md hover:bg-muted/50"
              >
                <div className="flex items-center gap-3">
                  <span
                    className="h-3 w-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: cat.color }}
                  />
                  <span className="text-sm font-medium">{cat.name}</span>
                  {cat.is_default && (
                    <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                      default
                    </span>
                  )}
                  {cat.exclude_from_stats && (
                    <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded flex items-center gap-0.5">
                      <EyeOff className="h-2.5 w-2.5" />
                      excluded from stats
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <Dialog
                    open={editingCategory?.id === cat.id}
                    onOpenChange={(open) => !open && setEditingCategory(null)}
                  >
                    <DialogTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0"
                        onClick={() => setEditingCategory(cat)}
                      >
                        <Pencil className="h-3 w-3" />
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Edit Category</DialogTitle>
                        <DialogDescription>
                          Update the name or color of this category.
                        </DialogDescription>
                      </DialogHeader>
                      {editingCategory && (
                        <CategoryForm
                          category={editingCategory}
                          onSave={(name, color, excludeFromStats) =>
                            updateMutation.mutate({
                              id: editingCategory.id,
                              data: {
                                name,
                                color,
                                exclude_from_stats: excludeFromStats,
                              },
                            })
                          }
                          onCancel={() => setEditingCategory(null)}
                          isSaving={updateMutation.isPending}
                        />
                      )}
                    </DialogContent>
                  </Dialog>

                  {!cat.is_default && (
                    <Dialog
                      open={deleteTarget?.id === cat.id}
                      onOpenChange={(open) => !open && setDeleteTarget(null)}
                    >
                      <DialogTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 text-destructive hover:text-destructive"
                          onClick={() => setDeleteTarget(cat)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Delete Category</DialogTitle>
                          <DialogDescription>
                            Are you sure you want to delete &quot;{cat.name}&quot;? This will remove
                            the category from all transactions that use it.
                          </DialogDescription>
                        </DialogHeader>
                        <DialogFooter>
                          <Button variant="outline" onClick={() => setDeleteTarget(null)}>
                            Cancel
                          </Button>
                          <Button
                            variant="destructive"
                            onClick={() => deleteMutation.mutate(cat.id)}
                            disabled={deleteMutation.isPending}
                          >
                            {deleteMutation.isPending ? "Deleting..." : "Delete"}
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

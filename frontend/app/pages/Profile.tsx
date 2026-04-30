import { useEffect, useMemo, useState } from "react";
import { getMyProfile, updateMyProfile, type ApiUser, formatApiError } from "../lib/api";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";
import { Separator } from "../components/ui/separator";
import { Badge } from "../components/ui/badge";
import { Shield, UserRound, Phone, Lock, Save, Loader2, Mail, AtSign, CheckCircle2 } from "lucide-react";

export function Profile() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [user, setUser] = useState<ApiUser | null>(null);

  const [form, setForm] = useState({
    username: "",
    email: "",
    first_name: "",
    last_name: "",
    phone_number: "",
    current_password: "",
    new_password: "",
    confirm_new_password: "",
    password: "",
  });

  const dirty = useMemo(() => {
    if (!user) return false;
    return (
      form.username !== (user.username ?? "") ||
      form.email !== (user.email ?? "") ||
      form.first_name !== (user.first_name ?? "") ||
      form.last_name !== (user.last_name ?? "") ||
      form.phone_number !== (user.phone_number ?? "") ||
      form.current_password.length > 0 ||
      form.new_password.length > 0 ||
      form.confirm_new_password.length > 0
    );
  }, [form, user]);

  const sensitiveChanged = useMemo(() => {
    if (!user) return false;
    return (
      form.username !== (user.username ?? "") ||
      form.email !== (user.email ?? "") ||
      form.new_password.length > 0 ||
      form.confirm_new_password.length > 0
    );
  }, [form, user]);

  const displayName = useMemo(() => {
    const full = `${form.first_name} ${form.last_name}`.trim();
    return full || form.username || "User";
  }, [form.first_name, form.last_name, form.username]);

  const initials = useMemo(() => {
    const source = `${form.first_name} ${form.last_name}`.trim() || form.username || "U";
    const parts = source.split(/\s+/).filter(Boolean);
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return source.slice(0, 2).toUpperCase();
  }, [form.first_name, form.last_name, form.username]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoading(true);
        const me = await getMyProfile();
        if (!mounted) return;
        setUser(me);
        setForm({
          username: me.username ?? "",
          email: me.email ?? "",
          first_name: me.first_name ?? "",
          last_name: me.last_name ?? "",
          phone_number: me.phone_number ?? "",
          current_password: "",
          new_password: "",
          confirm_new_password: "",
          password: "",
        });
      } catch (e) {
        setError(formatApiError(e));
      } finally {
        setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const onSave = async () => {
    if (!user) return;
    setError(null);
    setSuccess(null);

    if (form.new_password && form.new_password !== form.confirm_new_password) {
      setError("The new password and confirmation do not match.");
      return;
    }

    if (sensitiveChanged && !form.current_password.trim()) {
      setError("Current password is required to update username, email, or password.");
      return;
    }

    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        username: form.username,
        email: form.email,
        first_name: form.first_name || null,
        last_name: form.last_name || null,
        phone_number: form.phone_number || null,
        current_password: form.current_password || null,
        new_password: form.new_password || null,
        confirm_new_password: form.confirm_new_password || null,
      };

      const updated = await updateMyProfile(payload as any);
      setUser(updated);
      setForm((prev) => ({
        ...prev,
        current_password: "",
        new_password: "",
        confirm_new_password: "",
      }));
      setSuccess("Profile updated successfully.");
    } catch (e) {
      setError(formatApiError(e));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-slate-300">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading profile...
      </div>
    );
  }

  const inputClass = "h-11 rounded-xl border-slate-700 bg-slate-900/90 text-slate-100 placeholder:text-slate-500 focus-visible:border-indigo-400 focus-visible:ring-indigo-400/30";
  const labelClass = "mb-1.5 flex items-center gap-2 text-sm font-medium text-slate-300";

  return (
    <div className="flex w-full flex-col gap-3">
      <Card className="overflow-hidden border border-slate-800 bg-slate-900/70">
        <div className="relative">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_10%_10%,rgba(59,130,246,0.18),transparent_40%),radial-gradient(circle_at_90%_20%,rgba(16,185,129,0.15),transparent_35%)]" />
          <div className="relative flex flex-col gap-2.5 p-4 sm:flex-row sm:items-center sm:justify-between lg:p-4.5">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-indigo-400/30 bg-indigo-500/20 text-base font-semibold text-indigo-200">
                {initials}
              </div>
              <div>
                <div className="flex items-center gap-2 text-lg text-white">
                  <UserRound className="h-5 w-5 text-indigo-300" />
                  Profile Settings
                </div>
                <div className="mt-1 text-xs text-slate-300 sm:text-sm">
                  Keep account details accurate and secure for smooth analysis workflow.
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="border-slate-600/80 bg-slate-900/50 text-slate-200">
                <Shield className="mr-2 h-3.5 w-3.5" />
                Secure update flow
              </Badge>
              <Badge variant="outline" className="border-emerald-600/40 bg-emerald-900/20 text-emerald-300">
                {displayName}
              </Badge>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid gap-3 lg:grid-cols-[1.4fr_0.95fr] lg:gap-4">
        <Card className="overflow-hidden border border-slate-800 bg-slate-900/65">
          <div className="border-b border-slate-800 bg-slate-950/40 px-5 py-3.5">
            <div className="text-lg font-medium text-white">Personal & Contact Details</div>
            <div className="mt-1 text-sm text-slate-400">Update identity and contact fields used across the platform.</div>
          </div>

          <div className="p-4 lg:p-4.5">
            {error && (
              <div className="mb-2.5 whitespace-pre-wrap rounded-xl border border-red-900/70 bg-red-950/45 px-4 py-2 text-sm text-red-200">
                {error}
              </div>
            )}
            {success && (
              <div className="mb-2.5 flex items-center gap-2 rounded-xl border border-emerald-700/60 bg-emerald-950/35 px-4 py-2 text-sm text-emerald-200">
                <CheckCircle2 className="h-4 w-4" />
                {success}
              </div>
            )}

            <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
              <div>
                <label className={labelClass}>First name</label>
                <Input
                  className={inputClass}
                  value={form.first_name}
                  onChange={(e) => setForm((p) => ({ ...p, first_name: e.target.value }))}
                  placeholder="John"
                />
              </div>
              <div>
                <label className={labelClass}>Last name</label>
                <Input
                  className={inputClass}
                  value={form.last_name}
                  onChange={(e) => setForm((p) => ({ ...p, last_name: e.target.value }))}
                  placeholder="Doe"
                />
              </div>

              <div>
                <label className={labelClass}>
                  <AtSign className="h-4 w-4 text-slate-400" />
                  Username
                </label>
                <Input
                  className={inputClass}
                  value={form.username}
                  onChange={(e) => setForm((p) => ({ ...p, username: e.target.value }))}
                  placeholder="username"
                />
              </div>
              <div>
                <label className={labelClass}>
                  <Mail className="h-4 w-4 text-slate-400" />
                  Email
                </label>
                <Input
                  className={inputClass}
                  value={form.email}
                  onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
                  placeholder="name@company.com"
                />
              </div>

              <div className="sm:col-span-2">
                <label className={labelClass}>
                  <Phone className="h-4 w-4 text-slate-400" />
                  Phone number
                </label>
                <Input
                  className={inputClass}
                  value={form.phone_number}
                  onChange={(e) => setForm((p) => ({ ...p, phone_number: e.target.value }))}
                  placeholder="+380..."
                />
                <div className="mt-1 text-xs text-slate-500">Optional, used for account contact and recovery workflow.</div>
              </div>
            </div>

            <Separator className="my-3.5 bg-slate-800" />

            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <Button
                onClick={onSave}
                disabled={saving || !dirty}
                className="h-10 rounded-xl bg-indigo-600 px-5 text-white hover:bg-indigo-500"
              >
                {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                {saving ? "Saving..." : "Save changes"}
              </Button>
              {!dirty && <div className="text-sm text-slate-500">No changes to save</div>}
            </div>
          </div>
        </Card>

        <Card className="overflow-hidden border border-slate-800 bg-slate-900/65">
          <div className="border-b border-slate-800 bg-slate-950/40 px-5 py-3.5">
            <div className="text-lg font-medium text-white">Security</div>
            <div className="mt-1 text-sm text-slate-400">Use a strong password and confirm sensitive changes.</div>
          </div>

          <div className="space-y-3.5 p-4 lg:p-4.5">
            <div>
              <label className={labelClass}>
                <Lock className="h-4 w-4 text-slate-400" />
                New password
              </label>
              <Input
                className={inputClass}
                type="password"
                value={form.new_password}
                onChange={(e) => setForm((p) => ({ ...p, new_password: e.target.value }))}
                placeholder="Enter a new password"
              />
            </div>

            <div>
              <label className={labelClass}>
                <Lock className="h-4 w-4 text-slate-400" />
                Confirm new password
              </label>
              <Input
                className={inputClass}
                type="password"
                value={form.confirm_new_password}
                onChange={(e) => setForm((p) => ({ ...p, confirm_new_password: e.target.value }))}
                placeholder="Repeat the new password"
              />
            </div>

            <div>
              <label className={labelClass}>
                <Lock className="h-4 w-4 text-slate-400" />
                Current password
              </label>
              <Input
                className={inputClass}
                type="password"
                value={form.current_password}
                onChange={(e) => setForm((p) => ({ ...p, current_password: e.target.value }))}
                placeholder="Required for username, email, or password changes"
              />
            </div>

            <div className="rounded-xl border border-slate-700/70 bg-slate-950/55 p-3 text-[11px] leading-5 text-slate-400">
              Security note: changing username, email, or password always requires current password verification.
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}


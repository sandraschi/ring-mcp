import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Wrench, Video, Shield, Settings } from "lucide-react";

export function Tools() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Tool Inventory</h2>
                    <p className="text-slate-400">Available portmanteau interfaces for Ring Security</p>
                </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">Video Proxy</CardTitle>
                        <Video className="h-4 w-4 text-emerald-500" />
                    </CardHeader>
                    <CardContent>
                        <p className="text-xs text-slate-400">Stream snapshots and live video threads</p>
                    </CardContent>
                </Card>
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">Security Control</CardTitle>
                        <Shield className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <p className="text-xs text-slate-400">Arm/disarm and motion management</p>
                    </CardContent>
                </Card>
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">Device Config</CardTitle>
                        <Settings className="h-4 w-4 text-purple-500" />
                    </CardHeader>
                    <CardContent>
                        <p className="text-xs text-slate-400">Manage doorbell chimes and alerts</p>
                    </CardContent>
                </Card>
            </div>

            <Card className="border-slate-800 bg-slate-950/50">
                <CardHeader>
                    <CardTitle className="text-white">Active Capabilities</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50 border border-slate-800">
                            <div className="flex items-center">
                                <Wrench className="h-4 w-4 text-slate-400 mr-3" />
                                <span className="text-sm font-medium text-slate-200">ring_status</span>
                            </div>
                            <span className="text-xs text-emerald-500 font-mono">READY</span>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

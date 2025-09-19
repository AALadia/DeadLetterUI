import React from "react";
import LocalEndpointMenu from "../components/LocalEndpointMenu";
import DevDataTable from "../components/DevDataTable";
import { Header } from "../components/Header";

export default function DevDataDashboard() {
  return (
    <div className="flex flex-col items-center min-h-screen bg-slate-50 p-4 w-full">
      <Header />
      <div className="container mx-auto w-full">
        <LocalEndpointMenu />
        <DevDataTable />
      </div>
    </div>
  );
}

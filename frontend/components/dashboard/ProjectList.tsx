"use client";

import React from "react";
import { motion } from "framer-motion";
import { ProjectCard } from "./ProjectCard";
import { useRouter } from "next/navigation";

interface ProjectListProps {
  jobs: any[];
  onDelete: (e: React.MouseEvent, projectId: string) => void;
  deletingProjectId: string | null;
}

export function ProjectList({ jobs, onDelete, deletingProjectId }: ProjectListProps) {
  const router = useRouter();

  return (
    <div className="space-y-4">
      {jobs.map((job, index) => (
        <motion.div
          key={job.id}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 + (index * 0.05), ease: "easeOut" }}
        >
          <ProjectCard
            job={job}
            onDelete={onDelete}
            isDeleting={deletingProjectId === job.project_id}
            onClick={() => router.push(`/dashboard/${job.id}`)}
          />
        </motion.div>
      ))}
    </div>
  );
}

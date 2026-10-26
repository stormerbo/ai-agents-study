import type { Project } from '@/content/curriculum/schema';

export function ProjectDetails({ project }: { project: Project }) {
  return (
    <details className="mt-3 rounded-md border border-border/70 px-3 py-2.5 text-sm">
      <summary className="cursor-pointer font-medium">查看项目要求与验收细则</summary>
      <div className="mt-4 space-y-4 leading-relaxed">
        <section>
          <h3 className="font-medium">交付要求</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-muted-foreground">
            {project.requirements.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
        <section>
          <h3 className="font-medium">约束</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-muted-foreground">
            {project.constraints.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
        <section>
          <h3 className="font-medium">里程碑</h3>
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-muted-foreground">
            {project.milestones.map((milestone) => (
              <li key={milestone.id}>
                <span className="font-medium text-foreground">{milestone.title}：</span>
                {milestone.detail}
              </li>
            ))}
          </ol>
        </section>
        {project.hardGates && project.hardGates.length > 0 && (
          <section className="rounded-md border border-amber-500/40 bg-amber-500/5 p-3">
            <h3 className="font-medium">独立硬性门槛</h3>
            <p className="mt-1 text-xs text-muted-foreground">
              以下安全与状态不变量不能由其他评分项抵消。
            </p>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              {project.hardGates.map((gate) => (
                <li key={gate}>{gate}</li>
              ))}
            </ul>
          </section>
        )}
        {project.referenceImpl && (
          <section>
            <h3 className="font-medium">参考实现</h3>
            <p className="mt-1 text-muted-foreground">{project.referenceImpl.notes}</p>
            {project.referenceImpl.repo && (
              <p className="mt-1 text-xs text-muted-foreground">
                项目目录：<code>{project.referenceImpl.repo}</code>
              </p>
            )}
            {project.referenceImpl.command && (
              <pre className="mt-2 overflow-x-auto rounded-md bg-muted/50 p-3 text-xs">
                <code>{project.referenceImpl.command}</code>
              </pre>
            )}
          </section>
        )}
        <section>
          <h3 className="font-medium">自评 rubric</h3>
          <ul className="mt-2 space-y-3">
            {project.rubric.map((item) => (
              <li key={item.id}>
                <p className="font-medium">{item.criteria}</p>
                <ol className="mt-1 list-decimal space-y-0.5 pl-5 text-muted-foreground">
                  {item.levels.map((level) => (
                    <li key={level.score}>
                      {level.score} 分：{level.descriptor}
                    </li>
                  ))}
                </ol>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </details>
  );
}

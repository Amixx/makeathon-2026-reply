import { Flex } from "@adobe/react-spectrum";
import DiscoverList from "../components/discover/DiscoverList";
import PlanPanel from "../components/discover/PlanPanel";
import { useDiscover } from "../hooks/useDiscover";
import { usePlan } from "../hooks/usePlan";

export default function Chat() {
  const discover = useDiscover();
  const plan = usePlan();

  return (
    <Flex direction="column" height="calc(100vh - 4rem)">
      <DiscoverList
        items={discover.items}
        isLoading={discover.isLoading}
        error={discover.error}
        onRefresh={discover.refresh}
        onSelect={plan.open}
      />
      {plan.item && (
        <PlanPanel
          item={plan.item}
          segments={plan.segments}
          output={plan.output}
          completedSteps={plan.completedSteps}
          onToggleStep={plan.toggleStep}
          isStreaming={plan.isStreaming}
          error={plan.error}
          onClose={plan.close}
          onRetry={plan.retry}
        />
      )}
    </Flex>
  );
}

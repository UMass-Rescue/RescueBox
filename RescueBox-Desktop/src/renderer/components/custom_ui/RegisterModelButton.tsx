import { Link } from 'react-router-dom';
import { Button } from '../ui/button';
import { ConnectIcon } from '../icons/ConnectIcon';

export default function RegisterModelButton({
  replace = false,
}: {
  replace: boolean;
}) {
  return (
    <Link
      to="/registration/new_model"
      replace={replace}
      className="inline-flex"
    >
      <Button
        className="hover:-translate-y-0.5  flex flex-row gap-2  "
        variant="default"
        size="lg"
      >
        <p>Register a Model</p>
        <div className="-mr-1">
          <ConnectIcon className="fill-white" />
        </div>
      </Button>
    </Link>
  );
}

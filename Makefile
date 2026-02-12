.PHONY: help build deploy test logs clean rebuild redeploy

help:
	@echo "Human Design - Makefile Commands"
	@echo ""
	@echo "Development:"
	@echo "  make build-dev      Build dev Docker image"
	@echo "  make build-runtime  Build runtime Docker image"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy         Deploy to AWS Lambda"
	@echo "  make redeploy       Rebuild and deploy (full pipeline)"
	@echo ""
	@echo "Verification:"
	@echo "  make test           Test API endpoint"
	@echo "  make logs           View Lambda logs"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          Remove local Docker images"

# Build targets
build-dev:
	@echo "Building dev Docker image..."
	docker build --target=dev -t hd-dev:latest .

build-runtime:
	@echo "Building runtime Docker image..."
	docker build --target=runtime -t hd-runtime:latest .

build: build-runtime
	@echo "Runtime image built successfully"

# Deploy targets
deploy:
	@echo "Deploying HumanDesignStack to AWS..."
	cd cdk && cdk deploy HumanDesignStack --require-approval=never --region us-east-1

redeploy: build deploy
	@echo "Redeploy complete!"

# Test targets
test:
	@echo "Testing API endpoint..."
	@curl -s -w "\nStatus: %{http_code}\n" -X GET https://lxmkhc0y2c.execute-api.us-east-1.amazonaws.com/

logs:
	@echo "Retrieving Lambda logs (last 50 lines)..."
	@aws logs tail /aws/lambda/HumanDesignStack-FastAPILambda1C6C33F7-NkuNo6V5u6Og

# Cleanup
clean:
	@echo "Removing local Docker images..."
	docker rmi hd-dev:latest hd-runtime:latest || true
	@echo "Cleanup complete"

# Dev container
devcontainer:
	@echo "Rebuilding devcontainer..."
	code --remote-env-file=/dev/null --file-uri=vscode-remote://dev-container%2B7b22686f737450617468223a222f686f6d652f6e6e656962617565722f636f64652f68756d616e2d646573696e227d/home/nneibaue/code/human-design

# Synth target (without deploy)
synth:
	@echo "Synthesizing CDK stack..."
	cd cdk && cdk synth

# Local testing
test-handler:
	@echo "Testing handler import locally..."
	docker run --rm --entrypoint /bin/bash hd-runtime:latest -c "cd /app && python -c \"from handler import handler; print('✓ Handler imported successfully')\""

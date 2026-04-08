# CloudFormation to Terraform Converter - Demo Script

A step-by-step guide for demonstrating the CF-to-Terraform converter with Jenkins integration.

## Demo Overview

**Duration**: 5-10 minutes  
**Audience**: Technical team, stakeholders  
**Goal**: Showcase automated CloudFormation to Terraform migration using AI

---

## Pre-Demo Setup

### Before Starting
- [ ] Jenkins job created and configured
- [ ] AWS credentials (int-jenkins-user) configured in Jenkins
- [ ] Bedrock Claude access enabled in AWS
- [ ] Sample CloudFormation stack available (e.g., INT03-HOS-ISO-EC2)
- [ ] Browser tabs ready: Jenkins, AWS Console (optional)

---

## Demo Script

### Part 1: Introduction (1 minute)

**[Show Slide or Code]**

"Today I'll demonstrate our automated CloudFormation to Terraform conversion tool. This solution addresses a key challenge at SkyTouch: migrating hundreds of CloudFormation stacks to Terraform efficiently and safely."

**Key Points:**
- We have 100+ CloudFormation stacks across environments
- Manual conversion is time-consuming and error-prone
- Our solution uses AI (AWS Bedrock with Claude) to automate conversion
- Includes validation and best practices analysis

---

### Part 2: Why Consider Terraform? (1 minute)

**[Show simple comparison or keep it conversational]**

"CloudFormation works well for us, but Terraform offers some interesting advantages worth exploring:"

**Key Advantages:**

**1. Drift Detection & Management** ⭐ **(Our Biggest Pain Point)**
- CloudFormation drift detection is limited and manual
- Terraform refresh shows real-time state differences
- Easy to see what changed outside of templates
- `terraform plan` always shows current vs desired state
- Much easier to fix drift issues

"We've all experienced this - someone makes a manual change in the console, and suddenly our CloudFormation stack is out of sync. With Terraform, you run `terraform plan` and immediately see what drifted."

**2. Better Preview of Changes**
- `terraform plan` shows exactly what will change before applying
- CloudFormation change sets are less detailed
- Easier to catch mistakes before they happen

**3. Multi-Cloud Ready**
- Same tool for AWS, Azure, GCP if we expand
- Manage Kubernetes, databases, SaaS tools
- One language for all infrastructure

**4. Larger Community**
- More examples and modules available
- Easier to find solutions online
- Growing industry standard

**Note**: This is about exploring options, not replacing everything immediately. This tool makes it easy to test Terraform with our existing stacks.

---

### Part 3: Our Solution - Architecture (1 minute)

**[Show Architecture Diagram or List]**

"Our solution has 3 phases:"

**Phase 1: Fetch CloudFormation Templates**
- Connects to AWS using Jenkins credentials
- Fetches templates from live stacks
- Caches for faster testing

**Phase 2: AI-Powered Conversion**
- Sends template to AWS Bedrock (Claude)
- AI analyzes CloudFormation structure
- Generates complete Terraform configuration
- Creates suggestions and best practices

**Phase 3: Validation**
- Runs terraform init, validate, and plan
- Captures results for review
- No changes applied automatically (safety first)

---

### Part 4: Live Demo - Jenkins (5 minutes)

#### Step 1: Navigate to Jenkins

**[Open Jenkins]**

"Let's see this in action. I'm opening our Jenkins job: 'CF-to-Terraform-Converter'"

**[Click on Job]**

#### Step 2: Build with Parameters

**[Click "Build with Parameters"]**

"The job has a simple interface with 4 parameters:"

**Fill in parameters**:
- **STACK_NAME**: `INT03-HOS-ISO-EC2` (or your stack)
- **AWS_ENV**: Select `int` from dropdown
- **ACTION**: Select `convert-and-plan`
- **AWS_REGION**: Leave as `us-west-2`

"Let me explain these choices:
- STACK_NAME: The CloudFormation stack we want to convert
- AWS_ENV: Which environment credentials to use
- ACTION: We'll do convert-and-plan to see validation
- REGION: Where the stack lives"

**[Click "Build"]**

#### Step 3: Watch Build Progress

**[Show Build Progress]**

"The pipeline has multiple stages:"

1. **Validate** - Checks parameters ✓
2. **Checkout** - Gets code from Git ✓
3. **Convert CF to Terraform** - Running...
   - "Building Docker image with Python dependencies"
   - "Connecting to AWS with Jenkins credentials"
   - "Sending template to Bedrock AI"
   - "Claude analyzes and converts to Terraform"
   - "Generating HTML report"
4. **Terraform Plan** - Running...
   - "Building Terraform Docker image"
   - "Running terraform init"
   - "Running terraform validate"
   - "Running terraform plan"

**[Wait for completion - ~2 minutes]**

"While this runs, let me highlight the key technologies:
- Docker for isolated, reproducible environments
- AWS Bedrock with Claude 3.5 Sonnet for AI conversion
- Jenkins credentials for secure AWS access
- Terraform in Docker for validation"

#### Step 4: View Results

**[Build Complete - Click "Conversion Report"]**

"Perfect! The build completed successfully. Let's look at the results."

**[Open Conversion Report]**

##### Section 1: Summary

"At the top, we see key metrics:
- 5 CloudFormation resources converted
- 6 Terraform files generated
- AI response was thorough"

##### Section 2: Generated Files

**[Scroll to Files section]**

"The converter generated all necessary Terraform files:
- ✓ main.tf - Main resource definitions
- ✓ variables.tf - Input variables
- ✓ outputs.tf - Output values
- ✓ provider.tf - AWS provider configuration
- ✓ terraform.tfvars.example - Example values
- ✓ conversion_notes.md - Manual steps from AI"

##### Section 3: Quality Checks

"All quality checks passed - every required file was generated."

##### Section 4: SkyTouch Metadata

**[Show metadata table]**

"The tool automatically identified:
- App name: hos-iso
- Environment: INT
- App environment ID: int03
- All our standard tags are preserved"

##### Section 5: Code Snippets

**[Scroll through code]**

"Here's the actual Terraform code. Let's look at main.tf:
- Clean, readable Terraform syntax
- Proper resource blocks
- Comments explaining conversions
- Variables used instead of hardcoded values"

**[Show another file like variables.tf]**

"Variables are comprehensive with:
- Descriptions
- Types
- Default values where appropriate"

##### Section 6: AI Suggestions

**[Scroll to Suggestions section]**

"This is really powerful - the AI analyzed the generated code and provided:

**Warnings** - Critical issues to address:
- Hardcoded security group IDs
- Subnet IDs that need data sources

**Suggestions** - Code improvements:
- Use data sources for lookups
- Move hardcoded values to variables

**Best Practices** - SkyTouch-specific:
- Tag management
- State backend configuration
- Naming conventions

**Migration Checklist** - Step-by-step guide for safe deployment"

##### Section 7: Terraform Plan Output

**[Scroll to Plan section]**

"Finally, we see the terraform plan output:
- Terraform plan: 3 resources to add
- 0 to change, 0 to destroy
- Output values listed
- No errors in validation"

**[Highlight the plan details]**

"This validates that our Terraform code is syntactically correct and would create the intended resources."

---

### Part 5: Download Artifacts (1 minute)

**[Go back to build page]**

"All generated files are available as artifacts:"

**[Click "Build Artifacts" or show artifacts section]**

"The team can download:
- All .tf files
- conversion_notes.md
- terraform_suggestions.md
- ai_conversion_report.json
- Even the raw AI response for reference"

**[Show one file - like main.tf]**

"These files are ready to use - just download, review, and apply."

---

### Part 6: Benefits & Next Steps (1 minute)

**[Summarize]**

**Key Benefits:**

1. **Speed**: Converts in ~2 minutes vs hours manually
2. **Accuracy**: AI understands CloudFormation intrinsic functions
3. **Best Practices**: Includes SkyTouch standards automatically
4. **Safety**: Validates before any changes
5. **Guidance**: Provides suggestions and migration checklist
6. **Transparency**: Shows exactly what will change

**What We've Achieved:**
- ✅ Automated conversion workflow
- ✅ AI-powered analysis
- ✅ Docker-based isolation
- ✅ Jenkins integration
- ✅ Beautiful HTML reports
- ✅ Ready for production use

**Next Steps:**
1. Test with more complex stacks
2. Expand to QAT/PRD environments
3. Create Terraform state management strategy
4. Train team on Terraform basics
5. Begin gradual migration

---

## Demo Tips

### If Something Goes Wrong

**Build Fails:**
- Check AWS credentials in Jenkins
- Verify Bedrock access in AWS Console
- Review console output for specific error

**No Report:**
- Ensure HTML Publisher plugin is installed
- Check artifacts were archived

**Plan Fails:**
- This is expected for some stacks (Route53, etc.)
- Show that error is captured in report
- Explain manual fixes needed

### Backup Slides/Talking Points

Have ready:
- Architecture diagram
- Before/after code comparison
- Cost comparison (manual vs automated)
- Timeline for full migration

### Questions You Might Get

**Q: How accurate is the AI conversion?**
A: Very high - Claude understands CloudFormation syntax and best practices. Always review and test before applying.

**Q: What about complex stacks?**
A: Works well. AI handles intrinsic functions, nested stacks, and complex dependencies. Some manual review always needed.

**Q: Cost of Bedrock API?**
A: Minimal - ~$0.003 per 1K tokens. A stack conversion costs <$0.50.

**Q: Can we customize the conversion?**
A: Yes - prompts are configurable, and AI respects SkyTouch patterns.

**Q: What about rollback?**
A: CloudFormation stacks remain untouched. Terraform is net new. Easy to abandon if needed.

---

## Post-Demo Actions

**If Demo Goes Well:**
1. Share Conversion Report link
2. Schedule follow-up for team training
3. Identify pilot stacks for migration
4. Set up Terraform state backend

**Gather Feedback:**
- What features are most valuable?
- What concerns need addressing?
- What documentation is needed?

---

## Quick Command Reference

**Run Locally:**
```bash
cd cf-to-tf-converter
python cf_to_tf_converter.py --stack-name STACK --profile int
cd converter_output/STACK
terraform init
terraform plan
```

**Run in Jenkins:**
1. Open CF-to-Terraform-Converter job
2. Click "Build with Parameters"
3. Enter stack name and select environment
4. Click "Build"
5. View "Conversion Report" when complete

---

**Demo Success Checklist:**
- [ ] Jenkins job runs successfully
- [ ] HTML report displays correctly
- [ ] All sections visible (metrics, files, suggestions, plan)
- [ ] Terraform files are clean and readable
- [ ] AI suggestions make sense
- [ ] Audience understands value proposition
- [ ] Questions answered confidently

**Good luck with your demo!** 🚀

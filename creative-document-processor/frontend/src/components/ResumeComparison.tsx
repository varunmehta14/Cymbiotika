import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Button, 
  Container, 
  FormControl, 
  FormLabel, 
  Heading, 
  Textarea, 
  VStack, 
  Text, 
  Spinner, 
  useToast, 
  Card, 
  CardBody, 
  CardHeader, 
  Badge, 
  Flex,
  Progress,
  Select,
  Checkbox,
  CheckboxGroup,
  Stack
} from '@chakra-ui/react';
import ReactMarkdown from 'react-markdown';

import { Document } from '../types/documents';
import { fetchDocuments } from '../services/documentService';

interface ResumeComparisonProps {}

const ResumeComparison: React.FC<ResumeComparisonProps> = () => {
  const [jobDescription, setJobDescription] = useState('');
  const [resumes, setResumes] = useState<Document[]>([]);
  const [selectedResumes, setSelectedResumes] = useState<string[]>([]);
  const [isComparing, setIsComparing] = useState(false);
  const [progressStatus, setProgressStatus] = useState('');
  const [progressPercentage, setProgressPercentage] = useState(0);
  const [result, setResult] = useState<string | null>(null);
  const [selectAll, setSelectAll] = useState(false);
  const toast = useToast();

  // Fetch available resumes
  useEffect(() => {
    const getResumes = async () => {
      try {
        const documents = await fetchDocuments('resumes');
        setResumes(documents);
      } catch (error) {
        toast({
          title: 'Error fetching resumes',
          description: error instanceof Error ? error.message : 'Unknown error',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      }
    };

    getResumes();
  }, [toast]);

  // Handle selecting all resumes
  useEffect(() => {
    if (selectAll) {
      setSelectedResumes(resumes.map(resume => resume.id));
    } else if (selectedResumes.length === resumes.length) {
      // If all were selected and selectAll is now false, clear selection
      setSelectedResumes([]);
    }
  }, [selectAll, resumes]);

  // Handle comparison
  const handleCompare = async () => {
    if (!jobDescription.trim()) {
      toast({
        title: 'Job description required',
        description: 'Please enter a job description to compare resumes against',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    // Use all resumes if none selected
    const resumeIds = selectedResumes.length > 0 ? selectedResumes : null;

    setIsComparing(true);
    setProgressStatus('Starting comparison...');
    setProgressPercentage(10);
    setResult(null);

    try {
      // Set up SSE connection
      const eventSource = new EventSource(
        `/api/documents/compare-resumes?_=${Date.now()}`
      );

      // Send the request data
      const response = await fetch('/api/documents/compare-resumes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_description: jobDescription,
          document_ids: resumeIds,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to start comparison');
      }

      // Handle SSE events
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        // Update progress
        if (data.message) {
          setProgressStatus(data.message);
          // Increment progress (approximate)
          setProgressPercentage(prev => Math.min(prev + 10, 90));
        }
        
        // Handle final result
        if (event.type === 'result' && data.result) {
          setResult(data.result.final_answer);
          setProgressPercentage(100);
          setProgressStatus('Comparison complete!');
          eventSource.close();
          setIsComparing(false);
        }
      };

      // Handle errors
      eventSource.onerror = () => {
        eventSource.close();
        setIsComparing(false);
        toast({
          title: 'Error during comparison',
          description: 'There was an error during the resume comparison process',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      };
    } catch (error) {
      setIsComparing(false);
      toast({
        title: 'Error starting comparison',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  // Handle resume selection
  const handleResumeSelection = (value: string[]) => {
    setSelectedResumes(value);
    setSelectAll(value.length === resumes.length);
  };

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={8} align="stretch">
        <Heading as="h1" size="xl">Resume Comparison</Heading>
        <Text>
          Enter a job description below and select resumes to compare. The system will analyze and rank the best candidates for the position.
        </Text>

        {/* Job Description Input */}
        <FormControl isRequired>
          <FormLabel>Job Description</FormLabel>
          <Textarea
            placeholder="Paste the job description here..."
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            minH="200px"
            isDisabled={isComparing}
          />
        </FormControl>

        {/* Resume Selection */}
        <FormControl>
          <FormLabel>Select Resumes to Compare</FormLabel>
          <Checkbox 
            isChecked={selectAll} 
            onChange={(e) => setSelectAll(e.target.checked)}
            mb={2}
          >
            Select All ({resumes.length})
          </Checkbox>
          
          <Card variant="outline">
            <CardBody maxH="300px" overflowY="auto">
              <CheckboxGroup 
                value={selectedResumes}
                onChange={(value) => handleResumeSelection(value as string[])}
              >
                <Stack spacing={2}>
                  {resumes.map(resume => (
                    <Checkbox key={resume.id} value={resume.id}>
                      {resume.name || resume.filename}
                    </Checkbox>
                  ))}
                </Stack>
              </CheckboxGroup>
            </CardBody>
          </Card>
          <Text fontSize="sm" mt={1}>
            Leave all unselected to compare against all available resumes
          </Text>
        </FormControl>

        {/* Compare Button */}
        <Button 
          colorScheme="blue" 
          onClick={handleCompare} 
          isLoading={isComparing}
          loadingText="Comparing"
          size="lg"
        >
          Compare Resumes
        </Button>

        {/* Progress Indicator */}
        {isComparing && (
          <Box>
            <Text>{progressStatus}</Text>
            <Progress value={progressPercentage} size="sm" colorScheme="blue" mt={2} />
          </Box>
        )}

        {/* Results Section */}
        {result && (
          <Card variant="outline">
            <CardHeader>
              <Heading size="md">Comparison Results</Heading>
            </CardHeader>
            <CardBody>
              <Box className="markdown-content">
                <ReactMarkdown>{result}</ReactMarkdown>
              </Box>
            </CardBody>
          </Card>
        )}
      </VStack>
    </Container>
  );
};

export default ResumeComparison; 
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Welcome to BPS Enrollment Dashboard</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600">
            Dashboard components will be added here.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
